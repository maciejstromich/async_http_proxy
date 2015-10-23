# async_http_proxy

Simple Asyncronous HTTP Proxy using asyncio with /status returning uptime and transfered data in bytes.

## Docker

Docker container is built using python:3.5

`
docker build -t async_http_proxy .

docker run -e HTTP_PROXY_PORT=8080 -p 8080:8080 async_http_proxy
`

