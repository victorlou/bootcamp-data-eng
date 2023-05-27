# Data Engineering Bootcamp

This repository includes an academic data engineering project, for learning purposes, exercising concepts in data ingestion, cloud computing, and other best practices in data engineering.

The following project represents the final project of the course.

## Crypto currency trades for front-end application

### Project goal

A financial broker has realized the importance of including crypto currency as part of the pool of investiments for its clients. For this, having a reliable and up to date source of information regarding the different currencies that are currently being traded is indispensable.

This project will serve as the data pipeline for ingesting, storaging and making this information available in an analytical environment for any application. At the moment, it is assumed that this will be collected to be displayed on a front-end application, but this data should be ready to be manipuled if necessary and to used on business intelligence tools as well as to be consumed by a data science project.

### Expected results

For the successful completion of this project, the items on the following list must be achieved completely.

- Constant retrieval of information, with a maximum of 1 minute between the available data and the latest trade on any crypto currency available on [Mercado Bitcoin](https://www.mercadobitcoin.com.br/).
- Information available for querying in SQL
- A robust storage system to allow for querying of data in its most granular form for the last year and daily information for years prior.

### Service details

This project is being conceived with AWS in mind and the cloud services used are all from this provider.

- **Task orquestration/monitoring**: AWS Cloud Watch
- **Container management**: AWS ECS — Elastic Container Service
- **Data transmission**: AWS Kinesis Data Firehose
- **Storage**: AWS S3 — Simple Storage Service
- **Data manipulation**: AWS Glue (Job)
- **Data reference and metadata**: AWS Glue (Catalog)
- **Analytical environment**: AWS Athena

### Process outline

The flow of this data pipeline revolves mostly aroung the configuration and setup of all the AWS features. It also includes the scripts which will ingest and manipulate the data accordingly. The following image illustrates how all of these are connected. The dashed lines represent only intereaction between elements of the process, while the solid lines (along with the yellow stripes) indicate the flow direction of data.

<img src="https://github.com/victorlou/bootcamp-data-eng/blob/main/image.png?raw=true" width="700"/>

With this, the steps to be followed are:

1. Cloud Watch activates ECS every 15 seconds;
2. ECS executes python ingestion code to retrieve information from [Mercado Bitcoin](https://www.mercadobitcoin.com.br/);
3. ECS directs the collected information to Firehose;
4. Firehose gathers this information and streams it to an S3 bucket every 60 seconds, or once the gathered data (in JSON format) surpasses 5MB;
5. Cloud Watch activates Glue every 5 minutes;
6. Glue Job reorganizes the data from JSON to Snappy Parquet, so that these files are consistent in size (64 MB);
7. Glue Catalog indexes and references information both in JSON and Parquet;
8. Athena utilizes Glue Catalog's information to allow for querying.

A step further on this outline could include a procedure that manipulates the data further, so that the past information is stored in materialized views, avoiding having to query the entire S3 bucket to get historical data.
