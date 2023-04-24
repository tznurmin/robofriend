q_MONGO_USER=`jq --arg v "$MAIL_DB_USER" -n '$v'`
q_MONGO_PASSWORD=`jq --arg v "$MAIL_DB_PASSWORD" -n '$v'`
mongo -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" admin <<EOF
    use robomail;
    db.createUser({
        user: $q_MONGO_USER,
        pwd: $q_MONGO_PASSWORD,
        roles: ["readWrite"],
    });
EOF
