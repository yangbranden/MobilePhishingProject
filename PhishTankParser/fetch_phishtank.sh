curl -L -s https://data.phishtank.com/data/online-valid.xml.gz -o ./urls/online-valid.xml.gz
curl -L -s https://data.phishtank.com/data/online-valid.csv.gz -o ./urls/online-valid.csv.gz
curl -L -s https://data.phishtank.com/data/online-valid.json.gz -o ./urls/online-valid.json.gz
gzip -d --force ./urls/online-valid.xml.gz
gzip -d --force ./urls/online-valid.csv.gz
gzip -d --force ./urls/online-valid.json.gz