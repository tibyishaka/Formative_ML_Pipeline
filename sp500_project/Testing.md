## MySQL endpoints

### Create
curl -X POST http://127.0.0.1:5000/api/sql/records -H "Content-Type: application/json" -d "{\"ticker\":\"TEST\",\"date\":\"2024-01-01\",\"open\":100,\"high\":105,\"low\":99,\"close\":102,\"volume\":1000000}"

### List (first 5 AAPL records)
curl "http://127.0.0.1:5000/api/sql/records?ticker=AAPL&limit=5"

### Get one record (replace 1 with a real id returned above)
curl http://127.0.0.1:5000/api/sql/records/1

### Update
curl -X PUT http://127.0.0.1:5000/api/sql/records/1 -H "Content-Type: application/json" -d "{\"close\":999}"

### Delete
curl -X DELETE http://127.0.0.1:5000/api/sql/records/1

### Latest record
curl "http://127.0.0.1:5000/api/sql/records/latest?ticker=AAPL"

### Date range
curl "http://127.0.0.1:5000/api/sql/records/range?ticker=AAPL&start=2017-01-01&end=2017-03-01"


## MongoDB endpoints

### Create
curl -X POST http://127.0.0.1:5000/api/mongo/records -H "Content-Type: application/json" -d "{\"ticker\":\"TEST\",\"date\":\"2024-01-01T00:00:00\",\"open\":100,\"high\":105,\"low\":99,\"close\":102,\"volume\":1000000}"

### List
curl "http://127.0.0.1:5000/api/mongo/records?ticker=AAPL&limit=5"

### Get one (paste the _id returned from create or list)
curl http://127.0.0.1:5000/api/mongo/records/PASTE_ID_HERE

### Update
curl -X PUT http://127.0.0.1:5000/api/mongo/records/PASTE_ID_HERE -H "Content-Type: application/json" -d "{\"close\":999}"

### Delete
curl -X DELETE http://127.0.0.1:5000/api/mongo/records/PASTE_ID_HERE

### Latest record (REQUIRED)
curl "http://127.0.0.1:5000/api/mongo/records/latest?ticker=AAPL"

### Date range (REQUIRED)
curl "http://127.0.0.1:5000/api/mongo/records/range?ticker=AAPL&start=2017-01-01T00:00:00&end=2017-03-01T00:00:00"