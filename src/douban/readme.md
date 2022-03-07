# douban rent house

## scripts

### get the latest rent topics of beijingzufang

```shell
apikey=0df993c66c0c636e29ecbb5344252a4a
group=beijingzufang
curl https://api.douban.com/v2/group/$group/topics?apikey=$apikey > data/$group-latest.json
```
