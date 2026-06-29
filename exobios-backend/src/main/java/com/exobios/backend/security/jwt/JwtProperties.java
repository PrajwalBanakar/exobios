package com.exobios.backend.security.jwt;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Getter
@Setter
@ConfigurationProperties(prefix = "app.jwt")
public class JwtProperties {

    private String secret;
    private long accessTokenExpiryMs = 86400000L;
    private long refreshTokenExpiryMs = 604800000L;
}
