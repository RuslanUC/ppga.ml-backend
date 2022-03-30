DROP TABLE IF EXISTS `links`;
CREATE TABLE `links` (
  `code` longtext NOT NULL UNIQUE,
  `url` longtext NOT NULL,
  `uses` int NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;