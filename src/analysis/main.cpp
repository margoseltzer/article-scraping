#include "cpl/cpl_conn.hpp"
#include <fstream>

const char* prefix = "test";
const char* file_name = "data.txt";

struct bundle_labels {
    cpl_id_t id;
    std::map<int, int> label_map;
};

void fetch_data() {
    std::ofstream outfile (file_name);

    // Store what the labels are for all the bundles
    std::vector<bundle_labels> all_bundle_labels;

    // Connect to the cpl
    connect_cpl();

    // Get all the bundles in the database
    auto *bundles = new std::vector<cplxx_object_info>();
    get_all_bundles(prefix, bundles);

    for (const auto& bundle : *bundles) {
        std::map<int, std::string> object_types;
        cpl_id_t bundle_id = bundle.id;

        std::cout << "BUNDLE: " << bundle_id << "\n";

        // Get the objects in the bundle
        auto *objects = new std::vector<cplxx_object_info>();
        get_bundle_objects(bundle_id, objects);
        std::cout << "objects size: " << objects->size() << '\n';

        for (const auto& object : *objects) {
            std::cout << object.id << "\n";
            object_types.insert(std::pair<int,std::string>(object.id, std::to_string(object.type)));
        }

        // Get the relations
        auto *relations = new std::vector<cpl_relation_t>();
        get_bundle_relations(bundle_id, relations);
        std::cout << "relations size: " << relations->size() << '\n';

        // Add edge to the data file
        for (const auto& relation : *relations) {
            std::cout << relation.query_object_id << ", " << relation.other_object_id << "\n";

            int source_id = relation.query_object_id;
            int dest_id = relation.other_object_id;
            auto src_it = object_types.find(source_id);
            auto dest_it = object_types.find(dest_id);
            if (src_it != object_types.end() && dest_it != object_types.end()) {
                std::string relation_str = src_it->second + ":" + dest_it->second + ":" + std::to_string(relation.type);
                outfile << std::to_string(source_id) << "\t" << std::to_string(dest_id) << "\t" << relation_str << std::endl;
            } else {
                throw std::runtime_error("Bundle objects and relations are inconsistent");
            }
        }
    }
    outfile.close();
}

int main(int argc, const char ** argv) {
    fetch_data();
    return 0;
}
