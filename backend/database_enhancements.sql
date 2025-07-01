-- AI Training Database Schema Enhancements for Audico AI
-- Run these SQL commands on your existing OpenCart database

-- 1. AI Product Embeddings Table
CREATE TABLE IF NOT EXISTS `ai_product_embeddings` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `embedding_vector` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`embedding_vector`)),
  `specifications` text DEFAULT NULL,
  `use_cases` text DEFAULT NULL,
  `compatibility` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`compatibility`)),
  `features_extracted` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`features_extracted`)),
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_product` (`product_id`),
  KEY `idx_product_id` (`product_id`),
  KEY `idx_last_updated` (`last_updated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. AI Training Documents Table
CREATE TABLE IF NOT EXISTS `ai_training_documents` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `document_name` varchar(255) NOT NULL,
  `document_type` enum('pricelist','manual','specification','catalog','training_data','knowledge_base') NOT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `file_size` bigint(20) DEFAULT NULL,
  `file_hash` varchar(64) DEFAULT NULL,
  `content_text` longtext DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `processing_status` enum('pending','processing','completed','failed') DEFAULT 'pending',
  `error_message` text DEFAULT NULL,
  `uploaded_by` varchar(100) DEFAULT NULL,
  `upload_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `processed_date` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_document_type` (`document_type`),
  KEY `idx_processing_status` (`processing_status`),
  KEY `idx_upload_date` (`upload_date`),
  KEY `idx_file_hash` (`file_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. AI Training Text Chunks Table (for vector search)
CREATE TABLE IF NOT EXISTS `ai_training_chunks` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `document_id` bigint(20) NOT NULL,
  `chunk_index` int(11) NOT NULL,
  `chunk_text` text NOT NULL,
  `chunk_embedding` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`chunk_embedding`)),
  `chunk_metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`chunk_metadata`)),
  `token_count` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_document_id` (`document_id`),
  KEY `idx_chunk_index` (`chunk_index`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_chunks_document` FOREIGN KEY (`document_id`) REFERENCES `ai_training_documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. AI Chat Sessions Table
CREATE TABLE IF NOT EXISTS `ai_chat_sessions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(100) NOT NULL,
  `user_id` varchar(100) DEFAULT NULL,
  `category` varchar(50) DEFAULT NULL,
  `start_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_activity` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `total_messages` int(11) DEFAULT 0,
  `session_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`session_data`)),
  `status` enum('active','completed','abandoned') DEFAULT 'active',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_session` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_category` (`category`),
  KEY `idx_last_activity` (`last_activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. AI Chat Messages Table
CREATE TABLE IF NOT EXISTS `ai_chat_messages` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(100) NOT NULL,
  `message_index` int(11) NOT NULL,
  `role` enum('user','assistant','system') NOT NULL,
  `content` text NOT NULL,
  `intent_detected` varchar(100) DEFAULT NULL,
  `entities_extracted` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`entities_extracted`)),
  `products_mentioned` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`products_mentioned`)),
  `response_metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`response_metadata`)),
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_role` (`role`),
  KEY `idx_intent` (`intent_detected`),
  KEY `idx_timestamp` (`timestamp`),
  CONSTRAINT `fk_messages_session` FOREIGN KEY (`session_id`) REFERENCES `ai_chat_sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. AI Product Recommendations Table
CREATE TABLE IF NOT EXISTS `ai_product_recommendations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `source_product_id` int(11) NOT NULL,
  `recommended_product_id` int(11) NOT NULL,
  `recommendation_type` enum('similar','accessory','upgrade','alternative','bundle') NOT NULL,
  `confidence_score` decimal(3,2) DEFAULT NULL,
  `reasoning` text DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_source_product` (`source_product_id`),
  KEY `idx_recommended_product` (`recommended_product_id`),
  KEY `idx_recommendation_type` (`recommendation_type`),
  KEY `idx_confidence_score` (`confidence_score`),
  CONSTRAINT `fk_rec_source_product` FOREIGN KEY (`source_product_id`) REFERENCES `oc_product` (`product_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rec_recommended_product` FOREIGN KEY (`recommended_product_id`) REFERENCES `oc_product` (`product_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. AI Training Progress Table
CREATE TABLE IF NOT EXISTS `ai_training_progress` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `training_type` enum('product_embeddings','document_processing','recommendation_training','price_optimization') NOT NULL,
  `status` enum('not_started','in_progress','completed','failed') DEFAULT 'not_started',
  `progress_percentage` decimal(5,2) DEFAULT 0.00,
  `items_processed` int(11) DEFAULT 0,
  `total_items` int(11) DEFAULT 0,
  `start_time` timestamp NULL DEFAULT NULL,
  `completion_time` timestamp NULL DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_training_type` (`training_type`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. AI Performance Metrics Table
CREATE TABLE IF NOT EXISTS `ai_performance_metrics` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `metric_type` enum('search_accuracy','recommendation_relevance','pricing_accuracy','response_time','user_satisfaction') NOT NULL,
  `metric_value` decimal(10,4) NOT NULL,
  `measurement_date` date NOT NULL,
  `measurement_hour` tinyint(4) DEFAULT NULL,
  `category` varchar(50) DEFAULT NULL,
  `metadata` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`metadata`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_metric_type` (`metric_type`),
  KEY `idx_measurement_date` (`measurement_date`),
  KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes for better performance
ALTER TABLE `oc_product` ADD INDEX `idx_model_status` (`model`, `status`);
ALTER TABLE `oc_product` ADD INDEX `idx_price_quantity` (`price`, `quantity`);
ALTER TABLE `oc_product_description` ADD INDEX `idx_name_language` (`name`, `language_id`);

-- Insert initial training progress records
INSERT INTO `ai_training_progress` (`training_type`, `status`) VALUES
('product_embeddings', 'not_started'),
('document_processing', 'not_started'),
('recommendation_training', 'not_started'),
('price_optimization', 'not_started');
