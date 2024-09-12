curl -L -s http://data.phishtank.com/data/online-valid.xml.gz -o ./targets/online-valid.xml.gz
curl -L -s http://data.phishtank.com/data/online-valid.csv.gz -o ./targets/online-valid.csv.gz
curl -L -s http://data.phishtank.com/data/online-valid.json.gz -o ./targets/online-valid.json.gz
gzip -d --force online-valid.xml.gz
gzip -d --force online-valid.csv.gz
gzip -d --force online-valid.json.gz