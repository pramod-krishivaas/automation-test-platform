import api from "../api/axiosConfig";

const testCaseService = {

  listTestCases: async (params = {}) => {
    const response = await api.get("/test-cases", { params: { page_size: 20, ...params } });
    return response.data;
  },

  createTestCase: async (payload) => {
    const response = await api.post("/test-cases", payload);
    return response.data;
  },

  bulkUploadTestCases: async (file, applicationId, moduleId) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("application_id", applicationId);
    fd.append("module_id", moduleId);
    const response = await api.post("/test-cases/bulk-upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

};

export default testCaseService;
