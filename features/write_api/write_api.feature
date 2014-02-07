@use_write_api_client
Feature: the performance platform write api

    Scenario: hitting the health check url
         When I go to "/_status"
         then I should get back a status of "200"

    Scenario: posting to the health check URL
        Given I have the data in "dinosaur.json"
         when I post the data to "/_status"
         then I should get back a status of "405"

    Scenario: posting to a reserved bucket name
        Given I have the data in "dinosaur.json"
         when I post the data to "/_bucket"
         then I should get back a status of "404"

    Scenario: posting one object to a bucket
        Given I have the data in "dinosaur.json"
          and I have a bucket named "my_dinosaur_bucket"
          and I use the bearer token for the bucket
         when I post the data to "/my_dinosaur_bucket"
         then I should get back a status of "200"
         and  the stored data should contain "1" "name" equaling "t-rex"

    Scenario: posting a list of objects to a bucket
        Given I have the data in "dinosaurs.json"
          and I have a bucket named "my_dinosaur_bucket"
          and I use the bearer token for the bucket
         when I post the data to "/my_dinosaur_bucket"
         then I should get back a status of "200"
         and  the stored data should contain "2" "size" equaling "big"
         and  the stored data should contain "1" "name" equaling "microraptor"

    Scenario: tagging data with week start at
        Given I have the data in "timestamps.json"
          and I have a bucket named "data_with_times"
          and I use the bearer token for the bucket
         when I post the data to "/data_with_times"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"

    Scenario: posting to a bucket with data group and data type
        Given I have the data in "timestamps.json"
          and I have a bucket named "data_with_times"
          and I use the bearer token for the bucket
          and bucket setting data_group is "transaction"
          and bucket setting data_type is "timings"
         when I post to the specific path "/data/transaction/timings"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"



