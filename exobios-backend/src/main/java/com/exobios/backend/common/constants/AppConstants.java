package com.exobios.backend.common.constants;

public final class AppConstants {

    private AppConstants() {}

    public static final String API_VERSION      = "/api/v1";

    public static final int    DEFAULT_PAGE_SIZE = 20;
    public static final int    MAX_PAGE_SIZE      = 100;

    public static final String SYSTEM_USER = "SYSTEM";

    public static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String BEARER_PREFIX         = "Bearer ";

    public static final String ROLE_ASHA        = "ROLE_ASHA";
    public static final String ROLE_SUPER_ADMIN = "ROLE_SUPER_ADMIN";
}
