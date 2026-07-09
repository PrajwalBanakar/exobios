package com.exobios.backend.measures.controller;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.measures.dto.CreateMeasureRequest;
import com.exobios.backend.measures.dto.MeasureDto;
import com.exobios.backend.measures.dto.UpdateMeasureRequest;
import com.exobios.backend.measures.service.MeasureService;
import com.exobios.backend.testsupport.AbstractControllerTest;
import com.exobios.backend.testsupport.JwtTestSupport;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = MeasureController.class)
class MeasureControllerTest extends AbstractControllerTest {

    @MockBean
    private MeasureService measureService;

    private MeasureDto sampleMeasure(UUID id, UUID ashaId) {
        return MeasureDto.builder().id(id).assessmentId(UUID.randomUUID())
                .patientId(UUID.randomUUID()).ashaWorkerId(ashaId).action("Administered ORS").build();
    }

    @Test
    void createMeasure_withoutToken_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/measures").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void createMeasure_withValidRequest_returns201() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(measureService.createMeasure(any(), any())).thenReturn(sampleMeasure(UUID.randomUUID(), ashaId));

        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(UUID.randomUUID());
        req.setAction("Administered ORS");

        mockMvc.perform(post("/api/v1/measures")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.action").value("Administered ORS"));
    }

    @Test
    void createMeasure_withBlankAction_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(UUID.randomUUID());
        req.setAction(""); // @NotBlank

        mockMvc.perform(post("/api/v1/measures")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createMeasure_withoutAssessmentId_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAction("Administered ORS"); // assessmentId is @NotNull, left null

        mockMvc.perform(post("/api/v1/measures")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getMeasureById_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(measureService.getMeasureById(any(), any())).thenReturn(sampleMeasure(id, ashaId));

        mockMvc.perform(get("/api/v1/measures/{id}", id).header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    @Test
    void getAllMeasures_returns200WithPage() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        Page<MeasureDto> page = new PageImpl<>(List.of(sampleMeasure(UUID.randomUUID(), ashaId)), PageRequest.of(0, 20), 1);
        when(measureService.getAllMeasures(any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/measures").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.totalElements").value(1));
    }

    @Test
    void getAssessmentTimeline_returns200WithList() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID assessmentId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(measureService.getAssessmentTimeline(any(), any()))
                .thenReturn(List.of(sampleMeasure(UUID.randomUUID(), ashaId)));

        mockMvc.perform(get("/api/v1/assessments/{assessmentId}/measures", assessmentId).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data[0].action").value("Administered ORS"));
    }

    @Test
    void updateMeasure_withValidRequest_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(measureService.updateMeasure(any(), any(), any())).thenReturn(sampleMeasure(id, ashaId));

        UpdateMeasureRequest req = new UpdateMeasureRequest();
        req.setAction("Updated action");

        mockMvc.perform(put("/api/v1/measures/{id}", id)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk());
    }

    @Test
    void deleteMeasure_returns200() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");

        mockMvc.perform(delete("/api/v1/measures/{id}", UUID.randomUUID()).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    void deleteMeasure_asForbiddenRole_returns403() throws Exception {
        String bearer = JwtTestSupport.bearer(jwtTokenProvider, UUID.randomUUID(), "9876500000", "GUEST");

        mockMvc.perform(delete("/api/v1/measures/{id}", UUID.randomUUID()).header("Authorization", bearer))
                .andExpect(status().isForbidden());
    }
}
