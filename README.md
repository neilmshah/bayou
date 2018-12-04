# bayou
A prototype for replicated, eventually consistent storage system design implemented using bi-directional streaming on gRPC, restful services using flask-restful and in-memory storage on redis
#### Team Members: Neil Shah, Shabari Girish, Vishwanath Manvi, Priyal Agrawal


## Link to research paper on which the prototype is based
http://www.scs.stanford.edu/17au-cs244b/sched/readings/bayou.pdf

## Screenshots of usage


## Usage

#### Dependencies
- grpcio
- redis
- flask
- flask-restful
- yaml
- requests
- json
- termcolor

#### Configs
Check config.yaml to see/set configuration for clients and severs

#### Create proto files
 ```
 python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. a_e.proto
 ```
 
 #### Start server nodes (one terminal per server)
 ```python
 python3 server.py one
 python3 server.py two
 python3 server.py three
 ```
 
 #### Start clients (one terminal per user)
 ```python
 python3 client.py vish
 python3 client.py priyal
 ```
 





