# lawlibrary

Uses Aaron Swartz's html2text library to parse CAML found in `pubinfo_*.zip` files from https://downloads.leginfo.legislature.ca.gov/

##Requirements

Custom VPC in AWS with private and public subnets with NAT and Internet Gateways, with a VPC Endpoint interface to `com.amazonaws.us-west-1.elasticfilesystem` 