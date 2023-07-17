This URL explorer is running on Flask framework, and is connected to Redis used as a cache, and MongoDB as a Database  

To start the application, run `docker-compose up`
Note: you need to have Docker installed

The application has two public APIs, POST /scrape and GET /html

The POST /scrape API get a json containing the seed url from the request body  
example:
`curl --location 'localhost:5000/scrape' \
--header 'Content-Type: application/json' \
--data '{
    "url": "https://google.com/"
}'`

The scrape API, is using a Queue to manage the urls it need to crawl, and each url will be explored by a task managed by a Threadpool.

Each new links found in the HTML of an URL will be then added to the Queue.

Redis was used as a caching mechanism to not visit multiple times the same URL.
Redis uses a key-value schema, here the key is the URL and the value is the constant 'visited', this allow us to use Redis automatic expiration, which is set to 1h for our case. 

MongoDB is used for storing the URL, its associated raw HTML, and a timestamp
Thus each document contains three fields, url (indexed), content, and last_modified.


The GET /html API get a json containing the url which we want to retrieve its raw HTML  
example:
`curl --location --request GET 'localhost:5000/html' \
--header 'Content-Type: application/json' \
--data '{
    "url":"https://google.com"
}'`

Both API validate the URL provided and will return a 400 Bad Request if the url is not valid.

This /html API look up in mongoDB if the URL has its raw HTML, and return 400 Bad Request if it was not found

IMPROVEMENTS:
- use celery for handling tasks
- use robots.txt file from hosts, to browse the allowed path
- implement throttling and adhere to the website's politeness guidelines
- using a streaming HTML parser
- use asynchronous HTTP library
