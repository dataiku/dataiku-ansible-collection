Dataiku ansible modules examples
================================

This directory contains single file playbooks to show off the various modules.

# Examples

## Multi-node Design/Automation/API stack

Prerequisites: None

This playbook takes in a simple inventory of 4 nodes and deploys a Design node, an Automation node and 2 API Nodes, on for Development and on for Production. See the playbook file  `api_deployer_infra.yml` header for more details.

## Configure monitoring on DSS

Prerequisites: a configured DSS instance

This playbook takes a DSS node and configures all settings to provide some monitoring. See the playbook file `dss_monitoring.yml` header for more details.
