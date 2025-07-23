#!/bin/bash

wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; do
        echo "PostgreSQL is unavailable or database doesn't exist - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up and database exists - continuing"
}

wait_for_migrations() {
    echo "Checking if migrations are needed..."
    while true; do
        if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt alembic_version" | grep -q "alembic_version"; then
            current_version=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT version_num FROM alembic_version" | tr -d '[:space:]')
            latest_version=$(alembic heads | awk '{print $1}')

            if [ "$current_version" == "$latest_version" ]; then
                echo "Migrations are up to date."
                break
            else
                echo "Migrations are not up to date. Current: $current_version, Latest: $latest_version"
                sleep 5
            fi
        else
            echo "Alembic version table does not exist. Migrations needed."
            sleep 5
        fi
    done
}

main() {
    wait_for_postgres

    if [ "$RUN_MIGRATIONS" = "true" ]; then
        echo "Applying migrations..."
        alembic upgrade head

        echo "Loading initial data..."
        python src/database/startup_data.py
    else
        wait_for_migrations
    fi

    echo "Starting service..."
    exec "$@"
}

main "$@"