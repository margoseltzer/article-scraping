#include <backends/cpl-odbc.h>
#include <cpl-db-backend.h>
#include <cpl-exception.h>
#include <cpl.h>
#include <cplxx.h>
#include <iostream>
#include <string>
#include <vector>

using namespace std;

void connect_cpl();

void get_all_bundles(const char* prefix, vector<cplxx_object_info> *bundles);

void get_bundle_objects(cpl_id_t bundle_id, vector<cplxx_object_info> *objects);

void get_bundle_relations(cpl_id_t bundle_id, vector<prov_relation_data> *relations);