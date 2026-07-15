```sh
cd examples/download-data-noauth

docker build -t download-data-noauth:to-upload .
docker save -o download-data-noauth.tar download-data-noauth:to-upload
```