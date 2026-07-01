package com.exobios.backend.assessments.service;

import com.exobios.backend.assessments.dto.AssessmentDto;
import com.exobios.backend.assessments.dto.CreateAssessmentRequest;
import com.exobios.backend.assessments.dto.ExaminationFindingRequest;
import com.exobios.backend.assessments.dto.LegacyInformationRequest;
import com.exobios.backend.assessments.dto.MedicalHistoryRequest;
import com.exobios.backend.assessments.dto.SymptomRequest;
import com.exobios.backend.assessments.dto.UpdateAssessmentRequest;
import com.exobios.backend.assessments.dto.VitalsRequest;
import com.exobios.backend.assessments.entity.AiAssessmentResult;
import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.ExaminationFinding;
import com.exobios.backend.assessments.entity.LegacyInformation;
import com.exobios.backend.assessments.entity.MedicalHistory;
import com.exobios.backend.assessments.entity.Symptom;
import com.exobios.backend.assessments.entity.Vitals;
import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.mapper.AssessmentMapper;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.integration.ai.AiGateway;
import com.exobios.backend.integration.ai.AiRequest;
import com.exobios.backend.integration.ai.AiResponse;
import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.enums.Role;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.exobios.backend.audit.annotation.Auditable;
import com.exobios.backend.audit.entity.enums.AuditAction;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.Year;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class AssessmentService {

    private final AssessmentRepository assessmentRepository;
    private final PatientRepository    patientRepository;
    private final AssessmentMapper     assessmentMapper;
    private final AiGateway            aiGateway;

    // ── Create ────────────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.CREATE, entityType = "ASSESSMENT")
    @Transactional
    public AssessmentDto createAssessment(CreateAssessmentRequest request, UserPrincipal principal) {
        Patient patient = patientRepository.findById(request.getPatientId())
                .orElseThrow(() -> new ResourceNotFoundException("Patient", request.getPatientId()));

        UUID ashaWorkerId = resolveAshaWorkerId(request, principal, patient);

        Assessment assessment = new Assessment();
        assessment.setAssessmentNumber(generateAssessmentNumber());
        assessment.setPatientId(request.getPatientId());
        assessment.setAshaWorkerId(ashaWorkerId);
        assessment.setPatientComplaint(request.getPatientComplaint());
        assessment.setComplaintCategory(request.getComplaintCategory());
        assessment.setStatus(AssessmentStatus.DRAFT);
        assessment.setAssessedAt(request.getAssessedAt() != null ? request.getAssessedAt() : Instant.now());

        applySymptoms(assessment, request.getSymptoms());
        applyVitals(assessment, request.getVitals());
        applyMedicalHistory(assessment, request.getMedicalHistory());
        applyExaminationFinding(assessment, request.getExaminationFinding());
        applyLegacyInformation(assessment, request.getLegacyInformation());

        Assessment saved = assessmentRepository.save(assessment);
        log.info("Created assessment number={} patient={} ashaWorker={}",
                saved.getAssessmentNumber(), request.getPatientId(), ashaWorkerId);
        return assessmentMapper.toDto(saved);
    }

    // ── Read ──────────────────────────────────────────────────────────────────

    public AssessmentDto getAssessmentById(UUID id, UserPrincipal principal) {
        Assessment assessment = findOrThrow(id);
        assertOwnership(assessment, principal);
        return assessmentMapper.toDto(assessment);
    }

    public PageResponse<AssessmentDto> getPatientAssessments(UUID patientId, Pageable pageable,
                                                              UserPrincipal principal) {
        patientRepository.findById(patientId)
                .orElseThrow(() -> new ResourceNotFoundException("Patient", patientId));

        Page<Assessment> page;
        if (isAsha(principal)) {
            page = assessmentRepository.findAllByPatientIdAndAshaWorkerId(
                    patientId, principal.getId(), pageable);
        } else {
            page = assessmentRepository.findAllByPatientId(patientId, pageable);
        }
        return PageResponse.of(page.map(assessmentMapper::toDto));
    }

    // ── Update ────────────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.UPDATE, entityType = "ASSESSMENT")
    @Transactional
    public AssessmentDto updateAssessment(UUID id, UpdateAssessmentRequest request,
                                          UserPrincipal principal) {
        Assessment assessment = findOrThrow(id);
        assertOwnership(assessment, principal);
        assertDraft(assessment);

        if (request.getPatientComplaint() != null) {
            assessment.setPatientComplaint(request.getPatientComplaint());
        }
        if (request.getComplaintCategory() != null) {
            assessment.setComplaintCategory(request.getComplaintCategory());
        }
        if (request.getAssessedAt() != null) {
            assessment.setAssessedAt(request.getAssessedAt());
        }

        if (request.getSymptoms() != null) {
            assessment.getSymptoms().clear();
            applySymptoms(assessment, request.getSymptoms());
        }
        if (request.getVitals() != null) {
            applyVitals(assessment, request.getVitals());
        }
        if (request.getMedicalHistory() != null) {
            applyMedicalHistory(assessment, request.getMedicalHistory());
        }
        if (request.getExaminationFinding() != null) {
            applyExaminationFinding(assessment, request.getExaminationFinding());
        }
        if (request.getLegacyInformation() != null) {
            applyLegacyInformation(assessment, request.getLegacyInformation());
        }

        return assessmentMapper.toDto(assessmentRepository.save(assessment));
    }

    // ── Submit ────────────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.SUBMIT, entityType = "ASSESSMENT")
    @Transactional
    public AssessmentDto submitAssessment(UUID id, UserPrincipal principal) {
        Assessment assessment = findOrThrow(id);
        assertOwnership(assessment, principal);
        assertDraft(assessment);

        assessment.setStatus(AssessmentStatus.SUBMITTED);
        assessment.setSubmittedAt(Instant.now());

        // Synchronous placeholder: call AI gateway, gracefully fall back to PENDING on failure.
        AiAssessmentResult aiResult = callAiGateway(assessment);
        aiResult.setAssessment(assessment);
        assessment.setAiResult(aiResult);

        log.info("Submitted assessment id={} number={} aiStatus={}",
                id, assessment.getAssessmentNumber(), aiResult.getStatus());
        return assessmentMapper.toDto(assessmentRepository.save(assessment));
    }

    private AiAssessmentResult callAiGateway(Assessment assessment) {
        AiRequest request = AiRequest.from(assessment);
        long start = System.currentTimeMillis();
        AiResponse response;
        try {
            response = aiGateway.analyzeAssessment(request);
        } catch (Exception e) {
            log.warn("AI gateway error for assessment {}: {}", assessment.getId(), e.getMessage());
            response = AiResponse.placeholder();
        }
        long processingTimeMs = System.currentTimeMillis() - start;

        AiAssessmentResult result = new AiAssessmentResult();
        result.setStatus(response.getStatus() != null ? response.getStatus() : AiResultStatus.PENDING);
        result.setSummary(response.getSummary());
        result.setRiskLevel(response.getRiskLevel());
        result.setConfidenceScore(response.getConfidenceScore());
        result.setRedFlags(response.getRedFlags());
        result.setRecommendations(response.getRecommendations());
        result.setProcessingTimeMs(processingTimeMs);
        result.setModelVersion(response.getModelVersion());
        result.setGeneratedAt(Instant.now());
        result.setSource(response.getSource());
        return result;
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private UUID resolveAshaWorkerId(CreateAssessmentRequest request, UserPrincipal principal,
                                     Patient patient) {
        if (isAsha(principal)) {
            if (!patient.getAshaWorkerId().equals(principal.getId())) {
                throw new ForbiddenException("Access denied: this patient belongs to a different ASHA worker");
            }
            return principal.getId();
        }
        // SUPER_ADMIN: use provided ashaWorkerId, else inherit from patient
        return request.getAshaWorkerId() != null ? request.getAshaWorkerId() : patient.getAshaWorkerId();
    }

    private void assertOwnership(Assessment assessment, UserPrincipal principal) {
        if (isAsha(principal) && !assessment.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this assessment belongs to a different ASHA worker");
        }
    }

    private void assertDraft(Assessment assessment) {
        if (assessment.getStatus() != AssessmentStatus.DRAFT) {
            throw new BadRequestException(
                    "Assessment " + assessment.getAssessmentNumber() +
                    " cannot be modified — status is " + assessment.getStatus());
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }

    private Assessment findOrThrow(UUID id) {
        return assessmentRepository.findById(id)
                .orElseThrow(() -> new AssessmentNotFoundException(id));
    }

    private String generateAssessmentNumber() {
        String year   = String.valueOf(Year.now().getValue());
        String prefix = "ASMT-" + year + "-%";
        Integer lastSeq = assessmentRepository.findMaxSequenceByYearPrefix(prefix);
        int next = (lastSeq != null ? lastSeq : 0) + 1;
        return "ASMT-" + year + "-" + String.format("%06d", next);
    }

    // ── Sub-entity builders ───────────────────────────────────────────────────

    private void applySymptoms(Assessment assessment, List<SymptomRequest> requests) {
        if (requests == null || requests.isEmpty()) return;
        for (SymptomRequest req : requests) {
            Symptom symptom = new Symptom();
            symptom.setAssessment(assessment);
            symptom.setName(req.getName());
            symptom.setDuration(req.getDuration());
            symptom.setSeverity(req.getSeverity());
            symptom.setRemarks(req.getRemarks());
            assessment.getSymptoms().add(symptom);
        }
    }

    private void applyVitals(Assessment assessment, VitalsRequest req) {
        if (req == null) return;
        Vitals vitals = assessment.getVitals() != null ? assessment.getVitals() : new Vitals();
        vitals.setAssessment(assessment);
        vitals.setHeartRate(req.getHeartRate());
        vitals.setSpo2(req.getSpo2());
        vitals.setTemperature(req.getTemperature());
        vitals.setBloodPressureSystolic(req.getBloodPressureSystolic());
        vitals.setBloodPressureDiastolic(req.getBloodPressureDiastolic());
        vitals.setRespiratoryRate(req.getRespiratoryRate());
        vitals.setHeight(req.getHeight());
        vitals.setWeight(req.getWeight());
        vitals.setBmi(computeBmi(req));
        vitals.setBloodSugar(req.getBloodSugar());
        assessment.setVitals(vitals);
    }

    private void applyMedicalHistory(Assessment assessment, MedicalHistoryRequest req) {
        if (req == null) return;
        MedicalHistory mh = assessment.getMedicalHistory() != null
                ? assessment.getMedicalHistory() : new MedicalHistory();
        mh.setAssessment(assessment);
        mh.setPastIllnesses(req.getPastIllnesses());
        mh.setCurrentMedications(req.getCurrentMedications());
        mh.setAllergies(req.getAllergies());
        mh.setFamilyHistory(req.getFamilyHistory());
        mh.setSurgeryHistory(req.getSurgeryHistory());
        mh.setHabits(req.getHabits());
        assessment.setMedicalHistory(mh);
    }

    private void applyExaminationFinding(Assessment assessment, ExaminationFindingRequest req) {
        if (req == null) return;
        ExaminationFinding ef = assessment.getExaminationFinding() != null
                ? assessment.getExaminationFinding() : new ExaminationFinding();
        ef.setAssessment(assessment);
        ef.setGeneralAppearance(req.getGeneralAppearance());
        ef.setConsciousness(req.getConsciousness());
        ef.setEdema(req.getEdema());
        ef.setSkin(req.getSkin());
        ef.setRespiratory(req.getRespiratory());
        ef.setCardiovascular(req.getCardiovascular());
        ef.setAbdominal(req.getAbdominal());
        ef.setNeurological(req.getNeurological());
        assessment.setExaminationFinding(ef);
    }

    private void applyLegacyInformation(Assessment assessment, LegacyInformationRequest req) {
        if (req == null) return;
        LegacyInformation li = assessment.getLegacyInformation() != null
                ? assessment.getLegacyInformation() : new LegacyInformation();
        li.setAssessment(assessment);
        li.setFamilySupport(req.getFamilySupport());
        li.setLivingConditions(req.getLivingConditions());
        li.setPreviousInterventions(req.getPreviousInterventions());
        li.setNotes(req.getNotes());
        assessment.setLegacyInformation(li);
    }

    private BigDecimal computeBmi(VitalsRequest req) {
        if (req.getBmi() != null) return req.getBmi();
        if (req.getHeight() != null && req.getWeight() != null
                && req.getHeight().compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal heightM = req.getHeight().divide(BigDecimal.valueOf(100), 4, RoundingMode.HALF_UP);
            return req.getWeight().divide(heightM.multiply(heightM), 2, RoundingMode.HALF_UP);
        }
        return null;
    }
}
