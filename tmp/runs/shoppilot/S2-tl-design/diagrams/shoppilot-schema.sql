-- ShopPilot MVP data model (S2 ER source). Generated to draw.io via er_from_sql.py (house style).
-- Audit columns (status/created_at/updated_at/deleted_at) on every table per the Standard Template.

CREATE TABLE `customer` (
    `customer_id`   UUID NOT NULL,
    `email`         VARCHAR(255) NOT NULL,
    `phone`         VARCHAR(32),
    `name`          VARCHAR(120) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `status`        ENUM('ACTIVE','DISABLED') NOT NULL,
    `created_at`    DATETIME NOT NULL,
    `updated_at`    DATETIME NOT NULL,
    `deleted_at`    DATETIME,
    PRIMARY KEY (`customer_id`)
);

CREATE TABLE `session` (
    `session_id`         UUID NOT NULL,
    `customer_id`        UUID NOT NULL,
    `family_id`          UUID NOT NULL,
    `refresh_token_hash` VARCHAR(255) NOT NULL,
    `access_expires_at`  DATETIME NOT NULL,
    `refresh_expires_at` DATETIME NOT NULL,
    `revoked_at`         DATETIME,
    `status`             ENUM('ACTIVE','REVOKED') NOT NULL,
    `created_at`         DATETIME NOT NULL,
    `updated_at`         DATETIME NOT NULL,
    `deleted_at`         DATETIME,
    PRIMARY KEY (`session_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
);

CREATE TABLE `cart` (
    `cart_id`     UUID NOT NULL,
    `customer_id` UUID NOT NULL,
    `expires_at`  DATETIME NOT NULL,
    `status`      ENUM('OPEN','CONVERTED','EXPIRED') NOT NULL,
    `created_at`  DATETIME NOT NULL,
    `updated_at`  DATETIME NOT NULL,
    `deleted_at`  DATETIME,
    PRIMARY KEY (`cart_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
);

CREATE TABLE `cart_item` (
    `cart_item_id` UUID NOT NULL,
    `cart_id`      UUID NOT NULL,
    `sku`          VARCHAR(64) NOT NULL,
    `quantity`     INT NOT NULL,
    `unit_price`   DECIMAL(10,2) NOT NULL,
    `status`       ENUM('ACTIVE','REMOVED') NOT NULL,
    `created_at`   DATETIME NOT NULL,
    `updated_at`   DATETIME NOT NULL,
    `deleted_at`   DATETIME,
    PRIMARY KEY (`cart_item_id`),
    FOREIGN KEY (`cart_id`) REFERENCES `cart` (`cart_id`)
);

CREATE TABLE `coupon` (
    `coupon_id`       UUID NOT NULL,
    `code`            VARCHAR(40) NOT NULL,
    `discount_amount` DECIMAL(10,2) NOT NULL,
    `valid_from`      DATETIME NOT NULL,
    `valid_to`        DATETIME NOT NULL,
    `max_uses`        INT,
    `status`          ENUM('ACTIVE','EXPIRED','DISABLED') NOT NULL,
    `created_at`      DATETIME NOT NULL,
    `updated_at`      DATETIME NOT NULL,
    `deleted_at`      DATETIME,
    PRIMARY KEY (`coupon_id`)
);

CREATE TABLE `stock` (
    `sku`        VARCHAR(64) NOT NULL,
    `available`  INT NOT NULL,
    `reserved`   INT NOT NULL,
    `sold`       INT NOT NULL,
    `status`     ENUM('ACTIVE','DISABLED') NOT NULL,
    `created_at` DATETIME NOT NULL,
    `updated_at` DATETIME NOT NULL,
    `deleted_at` DATETIME,
    PRIMARY KEY (`sku`)
);

CREATE TABLE `order` (
    `order_id`        UUID NOT NULL,
    `customer_id`     UUID NOT NULL,
    `coupon_id`       UUID,
    `order_no`        VARCHAR(24) NOT NULL,
    `state`           ENUM('AWAITING_PAYMENT','PAID','PACKING','SHIPPED','DELIVERED','PAYMENT_FAILED','PAYMENT_TIMEOUT','CANCELLED') NOT NULL,
    `subtotal`        DECIMAL(10,2) NOT NULL,
    `coupon_amount`   DECIMAL(10,2) NOT NULL,
    `shipping_cost`   DECIMAL(10,2) NOT NULL,
    `total`           DECIMAL(10,2) NOT NULL,
    `address_snapshot` TEXT NOT NULL,
    `status`          ENUM('ACTIVE','ARCHIVED') NOT NULL,
    `created_at`      DATETIME NOT NULL,
    `updated_at`      DATETIME NOT NULL,
    `deleted_at`      DATETIME,
    PRIMARY KEY (`order_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
    FOREIGN KEY (`coupon_id`) REFERENCES `coupon` (`coupon_id`)
);

CREATE TABLE `order_item` (
    `order_item_id` UUID NOT NULL,
    `order_id`      UUID NOT NULL,
    `sku`           VARCHAR(64) NOT NULL,
    `name`          VARCHAR(120) NOT NULL,
    `quantity`      INT NOT NULL,
    `unit_price`    DECIMAL(10,2) NOT NULL,
    `status`        ENUM('ACTIVE') NOT NULL,
    `created_at`    DATETIME NOT NULL,
    `updated_at`    DATETIME NOT NULL,
    `deleted_at`    DATETIME,
    PRIMARY KEY (`order_item_id`),
    FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`)
);

CREATE TABLE `payment` (
    `payment_id`        UUID NOT NULL,
    `order_id`          UUID NOT NULL,
    `amount`            DECIMAL(10,2) NOT NULL,
    `provider_event_id` VARCHAR(128),
    `state`             ENUM('AWAITING','SUCCESS','FAILURE','TIMEOUT') NOT NULL,
    `captured_at`       DATETIME,
    `status`            ENUM('ACTIVE') NOT NULL,
    `created_at`        DATETIME NOT NULL,
    `updated_at`        DATETIME NOT NULL,
    `deleted_at`        DATETIME,
    PRIMARY KEY (`payment_id`),
    FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`)
);

CREATE TABLE `reservation` (
    `reservation_id` UUID NOT NULL,
    `order_id`       UUID NOT NULL,
    `sku`            VARCHAR(64) NOT NULL,
    `quantity`       INT NOT NULL,
    `ttl_expires_at` DATETIME NOT NULL,
    `state`          ENUM('ACTIVE','RELEASED','CONVERTED') NOT NULL,
    `status`         ENUM('ACTIVE') NOT NULL,
    `created_at`     DATETIME NOT NULL,
    `updated_at`     DATETIME NOT NULL,
    `deleted_at`     DATETIME,
    PRIMARY KEY (`reservation_id`),
    FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`),
    FOREIGN KEY (`sku`) REFERENCES `stock` (`sku`)
);

CREATE TABLE `shipment` (
    `shipment_id`     UUID NOT NULL,
    `order_id`        UUID NOT NULL,
    `tracking_number` VARCHAR(64),
    `carrier`         VARCHAR(64),
    `status`          ENUM('PENDING','IN_TRANSIT','DELIVERED') NOT NULL,
    `created_at`      DATETIME NOT NULL,
    `updated_at`      DATETIME NOT NULL,
    `deleted_at`      DATETIME,
    PRIMARY KEY (`shipment_id`),
    FOREIGN KEY (`order_id`) REFERENCES `order` (`order_id`)
);

CREATE TABLE `audit_log` (
    `audit_id`     UUID NOT NULL,
    `event`        VARCHAR(64) NOT NULL,
    `actor`        VARCHAR(128) NOT NULL,
    `ts`           DATETIME NOT NULL,
    `subject_id`   VARCHAR(128) NOT NULL,
    `before_state` TEXT,
    `after_state`  TEXT,
    `outcome`      ENUM('SUCCESS','FAILURE','TIMEOUT') NOT NULL,
    `status`       ENUM('ACTIVE') NOT NULL,
    `created_at`   DATETIME NOT NULL,
    `updated_at`   DATETIME NOT NULL,
    `deleted_at`   DATETIME,
    PRIMARY KEY (`audit_id`)
);
