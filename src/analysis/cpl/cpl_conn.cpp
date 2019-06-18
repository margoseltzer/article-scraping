#include "cpl_conn.h"

void connect_cpl() {
    const char* cstring = "DSN=CPL;";
    cpl_db_backend_t* backend;
    cpl_return_t ret = cpl_create_odbc_backend(cstring, CPL_ODBC_GENERIC, &backend);
    if (ret != CPL_OK) {
        throw CPLException("Could not create ODBC connection. Error code: %d", ret);
    }

    ret = cpl_attach(backend);
    if (ret != CPL_OK) {
        throw CPLException("Could not open ODBC connection. Error code: %d", ret);
    }

    cpl_session_t session;
    ret = cpl_get_current_session(&session);
    if (ret != CPL_OK) {
        throw CPLException("Could not get current session. Error code: %d", ret);
    }
}

void get_all_bundles(const char* prefix, vector<cplxx_object_info> *bundles) {
    cpl_return_t ret = cpl_get_all_objects(prefix, 0, cpl_cb_collect_object_info_vector, bundles);
    if (ret != CPL_OK) {
        throw CPLException("Could not get all cpl objects. Error code: %d", ret);
    }
}

void get_bundle_objects(cpl_id_t bundle, vector<cplxx_object_info> *objects) {
    cpl_return_t ret = cpl_get_bundle_objects(bundle, cpl_cb_collect_object_info_vector, objects);
    if (ret != CPL_OK) {
        throw CPLException("Could not get bundle objects for bundle %d. Error code: %d", bundle, ret);
    }
}

void get_bundle_relations(cpl_id_t bundle, vector<prov_relation_data> *relations) {
    cpl_return_t ret = cpl_get_bundle_relations(bundle, cpl_cb_collect_relation_vector, relations);
    if (ret != CPL_OK) {
        throw CPLException("Could not get all bundle relations for bundle %d. Error code: %d", bundle, ret);
    }
}