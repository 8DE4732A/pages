unset http_proxy
unset https_proxy
python3 /home/pi/pages/spider.py
python3 /home/pi/pages/article.py
git add .
git commit -m "xxx"
git push