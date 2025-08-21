#!/usr/bin/env node
//
//  https://github.com/jens-maus/RaspberryMatic/blob/e7c5bf51ae973861a5ecf4fe26619b6d33ac86d5/buildroot-external/overlay/base-raspmatic_oci/bin/ha-proxy.js
// Copyright (c) 2021 Jens Maus <mail@jens-maus.de>
//
// Apache 2.0 License applies
//
//  Modifications to support HA ingress for ChirpStack
//
const express = require('/usr/local/lib/node_modules/express');
const { createProxyMiddleware } = require('/usr/local/lib/node_modules/http-proxy-middleware');
const ipaddr = require('/usr/local/lib/node_modules/ipaddr.js');
const HM_HAPROXY_SRC="172.30.32.2/32";
const TARGET_BACKEND = 'http://127.0.0.1:8080';

const nonGrpcProxy = createProxyMiddleware({
  pathFilter:'/',
  target: TARGET_BACKEND,
  changeOrigin: true,
  selfHandleResponse: true,
  on: {
      proxyRes (proxyRes, req, res) {

        // modify Location: response header
        if(typeof(proxyRes.headers.location) !== 'undefined') {
          var redirect = proxyRes.headers.location;
          redirect = req.headers['x-ingress-path'] + redirect;
          proxyRes.headers.location = redirect;
        }

        const bodyChunks = [];
        proxyRes.on('data', (chunk) => {
          bodyChunks.push(chunk);
        });
        proxyRes.on('end', () => {
          let body = Buffer.concat(bodyChunks);

          // forwarding source status
          res.status(proxyRes.statusCode);

          // forwarding source headers
          Object.keys(proxyRes.headers).forEach((key) => {
            res.append(key, proxyRes.headers[key]);
          });

          // modifying textual response bodies
          if (proxyRes.headers['content-type'] &&
              (
                proxyRes.headers['content-type'].includes('text/') ||
                proxyRes.headers['content-type'].includes('application/javascript') ||
                proxyRes.headers['content-type'].includes('application/json')
              )
              ) {

            // if this a textual response body we make sure to prepend the ingress path
            body = body.toString('latin1');

            body = body.replace(/(?<=["'= \\])\/(assets|src|node_modules)(\\?\/)/g,
                req.headers['x-ingress-path']+'/$1$2');

            // add ingress path to client api calls to server
            if(req.method=="GET" && req.path.indexOf("/assets/index")==0 && req.path.endsWith(".js")) {
              body = body.replaceAll('this.hostname_+"/api.',
                'this.hostname_+"'+req.headers['x-ingress-path']+'/api.');
            }
          
            if(proxyRes.headers['transfer-encoding'] == 'chunked') {
              res.end(new Buffer.from(body));
            } else {
              res.send(new Buffer.from(body));
              res.end();
            }
          } else {
            res.end(body);
          }
        });
    }
  },
});

function nonGrpcProxyHandler(req, res, next) {
  if(req.headers['content-type'] && (req.headers['content-type'].includes('application/grpc-web-text') || req.headers['content-type'].includes('application/grpc-web-text+proto'))) {
    next();
  } else {
    return nonGrpcProxy(req, res, next);
  }
}

const grpcProxy = createProxyMiddleware({
  target: TARGET_BACKEND,   // gRPC-Web capable backend
  changeOrigin: true,
  ws: false,
  selfHandleResponse: false,
  on: {
    ProxyReq: (proxyReq) => {
      proxyReq.removeHeader('accept-encoding'); // disable gzip, break streaming otherwise
    }
  }
});

function grpcProxyHandler(req, res, next) {
  return grpcProxy(req, res, next);
}

const app = express();
app.use((req, res, next) => {
  //Get whitelisted range
  let whitelisted_range = ipaddr.parseCIDR(HM_HAPROXY_SRC);
  //Get source IP
  let source_ip = ipaddr.parse(req.ip.split(':').pop());
  //Check if source IP in whitelisted range
  if(source_ip.match(whitelisted_range)) {
      // allowed, forward to next middleware (proxy)
    next();
  } else {
    // abort request with "403 Forbidden"
    res.status(403).end();
  }
}, nonGrpcProxyHandler, grpcProxyHandler);
app.listen(8099);
