#!Back up database:
export $(grep -v '^#' .env | xargs)
export $(grep -v '^#' .env.local | xargs)


#docker exec -t <database-container> pg_dump -c -U <database-_auth> -d <database-name> > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql
docker exec -t $(docker ps -aqf "name=$DB_NAME") pg_dump -c -U $DB_USER -d $DB_NAME > backups/dump_$(date +%d-%m-%Y"_"%H_%M_%S).sql
