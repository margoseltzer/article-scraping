#include <backends/cpl-odbc.h>
#include <cpl-db-backend.h>
#include <cpl-exception.h>
#include <cpl.h>
#include <cplxx.h>
#include <iostream>
#include <string>
#include <vector>

void connect_cpl();

void get_all_bundles(const char* prefix, std::vector<cplxx_object_info> *bundles);

void get_bundle_objects(cpl_id_t bundle_id, std::vector<cplxx_object_info> *objects);

void get_bundle_relations(cpl_id_t bundle_id, std::vector<cpl_relation_t> *relations);