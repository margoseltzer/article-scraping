#include "cpl/cpl_conn.h"

const char* prefix = "test";

struct bundle_labels {
    cpl_id_t id;
    map<int, int> label_map;
};

int main(int argc, const char ** argv) {
    // Store what the labels are for all the bundles
    vector<bundle_labels> all_bundle_labels;

    // Connect to the cpl
    connect_cpl();

    // Get all the bundles in the database
    auto *bundles = new vector<cplxx_object_info>();
    get_all_bundles(prefix, bundles);

    for (vector<cplxx_object_info>::const_iterator bundle = bundles->begin(); bundle != bundles->end(); ++bundle) {
        map<int, int> label_map;
        cpl_id_t bundle_id = bundle -> id;

        // Get the objects in the bundle & add to label map
        // The initial label is just the object type
        auto *objects = new vector<cplxx_object_info>();
        get_bundle_objects(bundle_id, objects);
        for (vector<cplxx_object_info>::const_iterator object = objects->begin(); object != objects->end(); ++object) {
            label_map.insert(pair<int,int>(object -> id, object -> type));
        }

        // Get the relations
        auto *relations = new vector<prov_relation_data>();
        get_bundle_relations(bundle_id, relations);

        bundle_labels b = {bundle_id, label_map};
        all_bundle_labels.push_back(b);
    }

    return 0;
}
