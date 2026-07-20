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

};

export default testCaseService;
