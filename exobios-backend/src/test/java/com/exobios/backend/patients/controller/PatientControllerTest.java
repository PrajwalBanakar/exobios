package com.exobios.backend.patients.controller;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.patients.dto.ChangePatientStatusRequest;
import com.exobios.backend.patients.dto.CreatePatientRequest;
import com.exobios.backend.patients.dto.PatientDto;
import com.exobios.backend.patients.dto.UpdatePatientRequest;
import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import com.exobios.backend.patients.service.PatientService;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = PatientController.class)
class PatientControllerTest extends AbstractControllerTest {

    @MockBean
    private PatientService patientService;

    private PatientDto samplePatient(UUID id, UUID ashaWorkerId) {
        return PatientDto.builder()
                .id(id).patientCode("PT-2026-000001").name("Priya Sharma")
                .age(28).gender(Gender.FEMALE).phone("9876543210")
                .ashaWorkerId(ashaWorkerId).status(PatientStatus.ACTIVE)
                .build();
    }

    private CreatePatientRequest validCreateRequest() {
        CreatePatientRequest req = new CreatePatientRequest();
        req.setName("Priya Sharma");
        req.setAge(28);
        req.setGender(Gender.FEMALE);
        req.setPhone("9876543210");
        return req;
    }

    // ── Unauthenticated / unauthorized access ───────────────────────────────────

    @Test
    void getAllPatients_withoutToken_returns401() throws Exception {
        mockMvc.perform(get("/api/v1/patients"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void getAllPatients_withNonAshaNonAdminRole_returns403() throws Exception {
        // Role encoded in the JWT is neither ASHA nor SUPER_ADMIN — @PreAuthorize on the
        // controller class ("hasAnyRole('ASHA','SUPER_ADMIN')") must reject it.
        String bearer = JwtTestSupport.bearer(jwtTokenProvider, UUID.randomUUID(), "9876500000", "DOCTOR");

        mockMvc.perform(get("/api/v1/patients").header("Authorization", bearer))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.success").value(false));
    }

    // ── List / search ────────────────────────────────────────────────────────────

    @Test
    void getAllPatients_asAsha_returns200() throws Exception {
        UUID ashaId = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        Page<PatientDto> page = new PageImpl<>(List.of(samplePatient(UUID.randomUUID(), ashaId)), PageRequest.of(0, 20), 1);
        when(patientService.getAllPatients(any(), any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/patients").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.content[0].name").value("Priya Sharma"))
                .andExpect(jsonPath("$.data.totalElements").value(1));
    }

    @Test
    void getAllPatients_asSuperAdmin_returns200() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        Page<PatientDto> page = new PageImpl<>(List.of(), PageRequest.of(0, 20), 0);
        when(patientService.getAllPatients(any(), any(), any())).thenReturn(PageResponse.of(page));

        mockMvc.perform(get("/api/v1/patients").header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    // ── Get by id ────────────────────────────────────────────────────────────────

    @Test
    void getPatientById_returns200WithPatient() throws Exception {
        UUID ashaId    = UUID.randomUUID();
        UUID patientId = UUID.randomUUID();
        String bearer  = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(patientService.getPatientById(any(), any())).thenReturn(samplePatient(patientId, ashaId));

        mockMvc.perform(get("/api/v1/patients/{id}", patientId).header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.name").value("Priya Sharma"));
    }

    @Test
    void getPatientById_withMalformedUuid_returns500_knownGap() throws Exception {
        // Documents current behavior rather than desired behavior: GlobalExceptionHandler
        // has no handler for MethodArgumentTypeMismatchException, so a malformed path
        // variable falls through to the generic 500 handler instead of a client-correctable
        // 400. Flagged in the final report as a gap; not fixed here since it would change
        // the API's error-handling behavior beyond what's needed for testability.
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");

        mockMvc.perform(get("/api/v1/patients/{id}", "not-a-uuid").header("Authorization", bearer))
                .andExpect(status().isInternalServerError());
    }

    // ── Create ───────────────────────────────────────────────────────────────────

    @Test
    void createPatient_withValidRequest_returns201() throws Exception {
        UUID ashaId   = UUID.randomUUID();
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(patientService.createPatient(any(), any())).thenReturn(samplePatient(UUID.randomUUID(), ashaId));

        mockMvc.perform(post("/api/v1/patients")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validCreateRequest())))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    void createPatient_withBlankName_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreatePatientRequest req = validCreateRequest();
        req.setName("");

        mockMvc.perform(post("/api/v1/patients")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.data.details.name").exists());
    }

    @Test
    void createPatient_withInvalidPhoneFormat_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreatePatientRequest req = validCreateRequest();
        req.setPhone("12345"); // doesn't match the Indian mobile pattern

        mockMvc.perform(post("/api/v1/patients")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createPatient_withAgeAbove120_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreatePatientRequest req = validCreateRequest();
        req.setAge(150);

        mockMvc.perform(post("/api/v1/patients")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createPatient_withMalformedAadhaar_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");
        CreatePatientRequest req = validCreateRequest();
        req.setAadhaarNumber("12345"); // must be exactly 12 digits

        mockMvc.perform(post("/api/v1/patients")
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    // ── Update ───────────────────────────────────────────────────────────────────

    @Test
    void updatePatient_withValidRequest_returns200() throws Exception {
        UUID ashaId    = UUID.randomUUID();
        UUID patientId = UUID.randomUUID();
        String bearer  = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        when(patientService.updatePatient(any(), any(), any())).thenReturn(samplePatient(patientId, ashaId));

        UpdatePatientRequest req = new UpdatePatientRequest();
        req.setName("Priya Sharma Updated");
        req.setGender(Gender.FEMALE);

        mockMvc.perform(put("/api/v1/patients/{id}", patientId)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk());
    }

    // ── Change status ────────────────────────────────────────────────────────────

    @Test
    void changeStatus_withValidRequest_returns200() throws Exception {
        UUID ashaId    = UUID.randomUUID();
        UUID patientId = UUID.randomUUID();
        String bearer  = JwtTestSupport.ashaBearer(jwtTokenProvider, ashaId, "9876543210");
        PatientDto updated = samplePatient(patientId, ashaId);
        when(patientService.changeStatus(any(), any(), any())).thenReturn(updated);

        ChangePatientStatusRequest req = new ChangePatientStatusRequest();
        req.setStatus(PatientStatus.INACTIVE);

        mockMvc.perform(patch("/api/v1/patients/{id}/status", patientId)
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk());
    }

    @Test
    void changeStatus_withMissingStatus_returns400ValidationError() throws Exception {
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");

        mockMvc.perform(patch("/api/v1/patients/{id}/status", UUID.randomUUID())
                        .header("Authorization", bearer)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }
}
