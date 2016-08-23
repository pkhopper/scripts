TMP="./xxxtransferdata.zip"
URL=https://raw.githubusercontent.com/pkhopper/vavava/master/vavava/transfer.py

if [ ! -f "./transfer.py" ]; then
  curl $URL -o "./transfer.py"
fi

if [! -f "$TMP" ]; then
  rm $TMP
fi

chmod +x "./transfer.py"

python transfer.py --force --server --ip 0.0.0.0 --port 1239 --outputfile $TMP

unzip $TMP
