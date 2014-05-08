@use_write_api_client
Feature: the performance platform write api

    Scenario: hitting the health check url
         When I go to "/_status"
         then I should get back a status of "200"

    Scenario: posting to the health check URL
        Given I have the data in "dinosaur.json"
         when I POST to the specific path "/_status"
         then I should get back a status of "405"

    Scenario: posting to a reserved data_set name
        Given I have the data in "dinosaur.json"
         when I POST to the specific path "/_data_set"
         then I should get back a status of "404"

    Scenario: posting one object to a data_set
        Given I have the data in "dinosaur.json"
          and I have a data_set named "my_dinosaur_data_set" with settings
            | key        | value       |
            | data_group | "dinosaur"  |
            | data_type  | "droppings" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/dinosaur/droppings"
         then I should get back a status of "200"
          and the stored data should contain "1" "name" equaling "t-rex"

    Scenario: posting a list of objects to a data_set
        Given I have the data in "dinosaurs.json"
          and I have a data_set named "my_dinosaur_data_set" with settings
            | key        | value       |
            | data_group | "dinosaur"  |
            | data_type  | "droppings" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/dinosaur/droppings"
         then I should get back a status of "200"
          and the stored data should contain "2" "size" equaling "big"
          and the stored data should contain "1" "name" equaling "microraptor"

    Scenario: tagging data with week start at
        Given I have the data in "timestamps.json"
          and I have a data_set named "data_with_times" with settings
            | key        | value   |
            | data_group | "data"  |
            | data_type  | "times" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/data/times"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"

    Scenario: posting to a data_set with data group and data type
        Given I have the data in "timestamps.json"
          and I have a data_set named "data_with_times" with settings
            | key        | value         |
            | data_group | "transaction" |
            | data_type  | "timings"     |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/transaction/timings"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"
