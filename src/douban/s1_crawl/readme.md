# scrape douban

## get the latest rent topics of group "beijingzufang" via api

```shell
apikey=0df993c66c0c636e29ecbb5344252a4a
group=beijingzufang
curl https://api.douban.com/v2/group/$group/topics?apikey=$apikey > s1_crawl/data/$group_$(date '+%m-%d').json
```
