package com.exobios.backend.common.utils;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

public final class DateUtils {

    private static final DateTimeFormatter ISO_DATE = DateTimeFormatter.ISO_LOCAL_DATE;

    private DateUtils() {}

    public static Instant now() {
        return Instant.now();
    }

    public static LocalDate today() {
        return LocalDate.now(ZoneOffset.UTC);
    }

    public static String formatDate(LocalDate date) {
        return date != null ? ISO_DATE.format(date) : null;
    }

    public static LocalDate parseDate(String dateStr) {
        return dateStr != null ? LocalDate.parse(dateStr, ISO_DATE) : null;
    }
}
