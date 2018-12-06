# Bayou
A prototype for replicated, eventually consistent storage system design implemented using bi-directional streaming on gRPC, restful services using flask-restful and in-memory storage on redis
#### Team Members: Neil Shah, Shabari Girish Ganapathy, Vishwanath Manvi, Priyal Agrawal


## Link to research paper on which the prototype is based
http://www.scs.stanford.edu/17au-cs244b/sched/readings/bayou.pdf

## Learnings
#### Neil Shah
- Theoritical understanding turned practical implementation of replicated, eventually consistent storage system design.
- Good grasp on conflict detection, resolution and replication consensus algorightms for distributed setups.
- During presentation walked the class through the demo of a replicated eventually consistent meeting room booking example that was developed from scratch using gRPC, flask-restful and redis. 
- Coded server side APIs for handling meeting requests, conflict detection and resolution. Solved multi-threaded resource management by using redis for storage. 

#### Priyal Agarawal
1. Understanding the concept of bayou system in detail.
2. Deep understanding of the weakly consistent storage systems through hands-on experience.
3. Worked on the bayou implementation specially the write commits and anti-entropy aspects of the prototype.
4. During the presentation, discussed the need for write commit and how servers determine the stability of writes.
5. Explained different approaches for write commitment along with their pros and cons.


#### Shabari Girish Ganapathy
1. Understanding and presenting the importance and usage of anit-entropy in Bayou system.
2. Wrote the code for anti-entropy functions between servers using grpc and handling initial conflicts between servers.

#### Vishwanath Manvi
1. Learnt how to read research papers as this itself is a skill in my opionion :-)
2. Learnt what Bayou is, how it works and how distributed concepts like eventual consistency,replication are achieved through Anti entropy, Primary server and write logs.
3. By collaborating with the team, was able come up with an implementation for the prototype using REST and gRPC.
4. I took up development of REST client and GET end point of REST server. REST client is a CLI utility used to make a room reservation and provide slots along with allows user to see the status of reservation. This was used in our demo.


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
 
## Screenshots of usage
  ##### 1. Start server nodes
  
 
 ![](./output/1.%20Starting%20servers.png)



  ##### 2. Start client and book a room
 
 
 ![](./output/2.%20Sending%20request%20through%20client.png)
 
 
 
  ##### 3. Anti-entropy between server nodes:
  
  
   ![](./output/3.%20Anti%20entropy%20between%20servers.png)




