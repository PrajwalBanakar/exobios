package com.exobios.backend.measures.service;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.measures.dto.CreateMeasureRequest;
import com.exobios.backend.measures.dto.MeasureDto;
import com.exobios.backend.measures.dto.UpdateMeasureRequest;
import com.exobios.backend.measures.entity.Measure;
import com.exobios.backend.measures.exception.MeasureNotFoundException;
import com.exobios.backend.measures.mapper.MeasureMapper;
import com.exobios.backend.measures.repository.MeasureRepository;
import com.exobios.backend.security.UserPrincipal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class MeasureServiceTest {

    @Mock private MeasureRepository    measureRepository;
    @Mock private AssessmentRepository assessmentRepository;
    @Mock private MeasureMapper        measureMapper;

    private MeasureService measureService;

    private final UUID ashaId    = UUID.randomUUID();
    private final UUID otherAsha = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        measureService = new MeasureService(measureRepository, assessmentRepository, measureMapper);
        lenient().when(measureMapper.toDto(any(Measure.class))).thenAnswer(inv -> {
            Measure m = inv.getArgument(0);
            return MeasureDto.builder().id(m.getId()).assessmentId(m.getAssessmentId())
                    .ashaWorkerId(m.getAshaWorkerId()).action(m.getAction()).build();
        });
    }

    private UserPrincipal asha(UUID id) { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }

    private Assessment submittedAssessmentOwnedBy(UUID owner) {
        Assessment a = new Assessment();
        ReflectionTestUtils.setField(a, "id", UUID.randomUUID());
        a.setPatientId(UUID.randomUUID());
        a.setAshaWorkerId(owner);
        a.setStatus(AssessmentStatus.SUBMITTED);
        return a;
    }

    private Measure existingMeasure(UUID id, UUID owner) {
        Measure m = new Measure();
        ReflectionTestUtils.setField(m, "id", id);
        m.setAssessmentId(UUID.randomUUID());
        m.setPatientId(UUID.randomUUID());
        m.setAshaWorkerId(owner);
        m.setAction("Administered ORS");
        return m;
    }

    // ── createMeasure — assessment must be non-DRAFT + owned ────────────────────

    @Test
    void createMeasure_onDraftAssessment_throwsBadRequest() {
        Assessment draft = submittedAssessmentOwnedBy(ashaId);
        draft.setStatus(AssessmentStatus.DRAFT);
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(draft.getId());
        req.setAction("Administered ORS");
        when(assessmentRepository.findById(draft.getId())).thenReturn(Optional.of(draft));

        assertThatThrownBy(() -> measureService.createMeasure(req, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
        verify(measureRepository, never()).save(any());
    }

    @Test
    void createMeasure_onAnotherAshasAssessment_throwsForbidden() {
        Assessment assessment = submittedAssessmentOwnedBy(otherAsha);
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(assessment.getId());
        req.setAction("Administered ORS");
        when(assessmentRepository.findById(assessment.getId())).thenReturn(Optional.of(assessment));

        assertThatThrownBy(() -> measureService.createMeasure(req, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void createMeasure_forUnknownAssessment_throwsAssessmentNotFound() {
        UUID assessmentId = UUID.randomUUID();
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(assessmentId);
        req.setAction("Administered ORS");
        when(assessmentRepository.findById(assessmentId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> measureService.createMeasure(req, asha(ashaId)))
                .isInstanceOf(AssessmentNotFoundException.class);
    }

    @Test
    void createMeasure_inheritsPatientAndAshaWorkerFromAssessment() {
        Assessment assessment = submittedAssessmentOwnedBy(ashaId);
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(assessment.getId());
        req.setAction("Administered ORS");
        when(assessmentRepository.findById(assessment.getId())).thenReturn(Optional.of(assessment));
        when(measureRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ArgumentCaptor<Measure> captor = ArgumentCaptor.forClass(Measure.class);
        measureService.createMeasure(req, asha(ashaId));

        verify(measureRepository).save(captor.capture());
        assertThat(captor.getValue().getPatientId()).isEqualTo(assessment.getPatientId());
        assertThat(captor.getValue().getAshaWorkerId()).isEqualTo(ashaId);
    }

    @Test
    void createMeasure_withoutImplementedBy_defaultsToPrincipalsPhone() {
        Assessment assessment = submittedAssessmentOwnedBy(ashaId);
        CreateMeasureRequest req = new CreateMeasureRequest();
        req.setAssessmentId(assessment.getId());
        req.setAction("Administered ORS");
        when(assessmentRepository.findById(assessment.getId())).thenReturn(Optional.of(assessment));
        when(measureRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ArgumentCaptor<Measure> captor = ArgumentCaptor.forClass(Measure.class);
        measureService.createMeasure(req, asha(ashaId));

        verify(measureRepository).save(captor.capture());
        assertThat(captor.getValue().getImplementedBy()).isEqualTo("9876543210");
    }

    // ── getMeasureById / updateMeasure / deleteMeasure — ownership ──────────────

    @Test
    void getMeasureById_asNonOwningAsha_throwsForbidden() {
        UUID id = UUID.randomUUID();
        when(measureRepository.findById(id)).thenReturn(Optional.of(existingMeasure(id, otherAsha)));

        assertThatThrownBy(() -> measureService.getMeasureById(id, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void getMeasureById_unknownId_throwsMeasureNotFound() {
        UUID id = UUID.randomUUID();
        when(measureRepository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> measureService.getMeasureById(id, asha(ashaId)))
                .isInstanceOf(MeasureNotFoundException.class);
    }

    @Test
    void updateMeasure_asNonOwningAsha_throwsForbiddenAndDoesNotSave() {
        UUID id = UUID.randomUUID();
        when(measureRepository.findById(id)).thenReturn(Optional.of(existingMeasure(id, otherAsha)));
        UpdateMeasureRequest req = new UpdateMeasureRequest();
        req.setAction("Updated");

        assertThatThrownBy(() -> measureService.updateMeasure(id, req, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
        verify(measureRepository, never()).save(any());
    }

    @Test
    void deleteMeasure_asOwningAsha_deletesSuccessfully() {
        UUID id = UUID.randomUUID();
        Measure measure = existingMeasure(id, ashaId);
        when(measureRepository.findById(id)).thenReturn(Optional.of(measure));

        measureService.deleteMeasure(id, asha(ashaId));

        verify(measureRepository).delete(measure);
    }

    @Test
    void deleteMeasure_asNonOwningAsha_throwsForbiddenAndDoesNotDelete() {
        UUID id = UUID.randomUUID();
        when(measureRepository.findById(id)).thenReturn(Optional.of(existingMeasure(id, otherAsha)));

        assertThatThrownBy(() -> measureService.deleteMeasure(id, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
        verify(measureRepository, never()).delete(any());
    }
}
