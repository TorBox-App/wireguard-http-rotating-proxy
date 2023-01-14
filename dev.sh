docker build . -t wireguard-rotator
docker run --rm -it \
  -p 8080:8080 \
  -e max=2 \
  --name=wireguarddev \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  -v $(pwd)/conf/:/conf/ \
  --sysctl="net.ipv4.conf.all.src_valid_mark=1" \
  wireguard-rotator