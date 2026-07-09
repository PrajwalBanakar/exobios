package com.exobios.backend.sos.controller;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.sos.dto.CreateSosRequest;
import com.exobios.backend.sos.dto.SosRecordDto;
import com.exobios.backend.sos.dto.UpdateSosStatusRequest;
import com.exobios.backend.sos.entity.enums.SosStatus;
import com.exobios.backend.sos.entity.enums.SosType;
import com.exobios.backend.sos.service.SosService;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = SosController.class)
class SosControllerTest extends AbstractControllerTest {

    @MockBean
    private SosService sosService;

    private SosRecordDto sampleSos(UUID id, UUID ashaId, SosStatus status) {
        return SosRecordDto.builder().id(id).patientId(UUID.randomUUID()).ashaWorkerId(ashaId)
                .type(SosType.MEDICAL_EMERGENCY).status(status).build();
    }

    private CreateSosRequest validRequest() {
        CreateSosRequest req = new CreateSosRequest();
        req.setPatientId(UUID.randomUUID());
        req.setType(SosType.MEDICAL_EMERGENCY);
        return req;
    }

    // ── Create — ASHA-only method-level @PreAuthorize override ──────────────────

    @Test
    void createSos_withoutToken_returns401() throws Exception {
        mockMvc.perform(post("/api/v1/sos").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void createSos_asAsha_returns201() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(sosService.createSos(any(), any())).thenReturn(sampleSos(UUID.randomUUID(), ashaId, SosStatus.ACTIVE));

        mockMvc.perform(post("/api/v1/sos")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.status").value("ACTIVE"));
    }

    @Test
    void createSos_asSuperAdmin_returns403() throws Exception {
        // SosController declares a method-level @PreAuthorize("hasRole('ASHA')") on
        // createSos that is *stricter* than the class-level hasAnyRole('ASHA','SUPER_ADMIN')
        // — even a SUPER_ADMIN must be rejected here.
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");

        mockMvc.perform(post("/api/v1/sos")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest())))
                .andExpect(status().isForbidden());
    }

    @Test
    void createSos_withoutPatientId_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreateSosRequest req = new CreateSosRequest();
        req.setType(SosType.MEDICAL_EMERGENCY); // patientId is @NotNull, left null

        mockMvc.perform(post("/api/v1/sos")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createSos_withOutOfRangeLatitude_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreateSosRequest req = validRequest();
        req.setLatitude(new java.math.BigDecimal("200")); // must be between -90 and 90

        mockMvc.perform(post("/api/v1/sos")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    // ── Read ─────────────────────────────────────────────────────────────────────

    @Test
    void getSosById_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(sosService.getSosById(any(), any())).thenReturn(sampleSos(id, ashaId, SosStatus.ACTIVE));

        mockMvc.perform(get("/api/v1/sos/{id}", id).header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    @Test
    void listSosRecords_asSuperAdmin_returns200() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        Page<SosRecordDto> page = new PageImpl<>(
                List.of(sampleSos(UUID.randomUUID(), UUID.randomUUID(), SosStatus.ACTIVE)), PageRequest.of(0, 20), 1);
        when(sosService.listSosRecords(any(), any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/sos").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.totalElements").value(1));
    }

    // ── Status update — SUPER_ADMIN or self-cancel by ASHA ──────────────────────

    @Test
    void updateSosStatus_asSuperAdmin_returns200() throws Exception {
        UUID id = UUID.randomUUID();
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        when(sosService.updateSosStatus(any(), any(), any()))
                .thenReturn(sampleSos(id, UUID.randomUUID(), SosStatus.RESOLVED));

        UpdateSosStatusRequest req = new UpdateSosStatusRequest();
        req.setStatus(SosStatus.RESOLVED);

        mockMvc.perform(patch("/api/v1/sos/{id}/status", id)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.status").value("RESOLVED"));
    }

    @Test
    void updateSosStatus_withoutStatus_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");

        mockMvc.perform(patch("/api/v1/sos/{id}/status", UUID.randomUUID())
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }
}
