import api from "../api/axiosConfig";

const catalogService = {

  listApplications: async () => {
    const response = await api.get("/applications", { params: { page_size: 100 } });
    return response.data;
  },

  createApplication: async (payload) => {
    const response = await api.post("/applications", payload);
    return response.data;
  },

  updateApplication: async (applicationId, payload) => {
    const response = await api.put(`/applications/${applicationId}`, payload);
    return response.data;
  },

  listModules: async (applicationId) => {
    const response = await api.get("/modules", { params: { application_id: applicationId, page_size: 200 } });
    return response.data;
  },

  createModule: async (payload) => {
    const response = await api.post("/modules", payload);
    return response.data;
  },

  listPriorities: async () => {
    const response = await api.get("/priorities", { params: { page_size: 100 } });
    return response.data;
  },

  discoverAutomationTests: async (path) => {
    const response = await api.get("/automation-tests", { params: { path } });
    return response.data;
  },

};

export default catalogService;
