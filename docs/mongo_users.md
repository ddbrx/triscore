# Mongo users

use admin
db.createUser(
  {
    user: "admin",
    pwd: passwordPrompt(),
    roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
  }
)

use ironman
db.createUser(
  {
    user: "data-loader",
    pwd:  passwordPrompt(),
    roles: [ { role: "readWrite", db: "ironman" }]
  }
)

use triscore
db.createUser(
  {
    user: "triscore-writer",
    pwd:  passwordPrompt(),
    roles: [ { role: "readWrite", db: "triscore" }, { role: "read", db: "ironman" } ]
  }
)

use triscore
db.createUser(
  {
    user: "triscore-reader",
    pwd:  passwordPrompt(),
    roles: [ { role: "read", db: "triscore" } ]
  }
)
