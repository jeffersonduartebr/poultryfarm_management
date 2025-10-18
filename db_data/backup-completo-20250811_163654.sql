/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.13-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: criacao_aves
-- ------------------------------------------------------
-- Server version	10.11.13-MariaDB-ubu2204

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `custos_lote`
--

DROP TABLE IF EXISTS `custos_lote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `custos_lote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lote_id` int(11) NOT NULL,
  `data` date DEFAULT NULL,
  `tipo_custo` varchar(100) DEFAULT NULL,
  `descricao` text DEFAULT NULL,
  `valor` float NOT NULL,
  PRIMARY KEY (`id`),
  KEY `lote_id` (`lote_id`),
  CONSTRAINT `custos_lote_ibfk_1` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `custos_lote`
--

LOCK TABLES `custos_lote` WRITE;
/*!40000 ALTER TABLE `custos_lote` DISABLE KEYS */;
/*!40000 ALTER TABLE `custos_lote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lotes`
--

DROP TABLE IF EXISTS `lotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `lotes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identificador_lote` varchar(100) NOT NULL,
  `linhagem` varchar(100) DEFAULT NULL,
  `aviario_alocado` varchar(50) DEFAULT NULL,
  `data_alojamento` date NOT NULL,
  `aves_alojadas` int(11) DEFAULT NULL,
  `status` enum('Ativo','Finalizado') DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `identificador_lote` (`identificador_lote`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lotes`
--

LOCK TABLES `lotes` WRITE;
/*!40000 ALTER TABLE `lotes` DISABLE KEYS */;
INSERT INTO `lotes` VALUES
(1,'Lote 06','Avifram GLC','02','2024-05-19',550,'Ativo'),
(2,'Lote 05','Novogen brawn','03','2023-09-19',500,'Ativo'),
(3,'Lote 7','Novogen Tinted','04','2025-02-11',690,'Ativo'),
(4,'Lote 07','Novogen Tinted','04','2025-02-11',690,'Finalizado');
/*!40000 ALTER TABLE `lotes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `metas_linhagem`
--

DROP TABLE IF EXISTS `metas_linhagem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `metas_linhagem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `linhagem` varchar(100) NOT NULL,
  `semana_idade` int(11) NOT NULL,
  `peso_medio_g` float DEFAULT NULL,
  `consumo_ave_dia_g` float DEFAULT NULL,
  `consumo_acum_g` float DEFAULT NULL,
  `mortalidade_acum_pct` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `metas_linhagem`
--

LOCK TABLES `metas_linhagem` WRITE;
/*!40000 ALTER TABLE `metas_linhagem` DISABLE KEYS */;
/*!40000 ALTER TABLE `metas_linhagem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producao_aves`
--

DROP TABLE IF EXISTS `producao_aves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `producao_aves` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lote_id` int(11) NOT NULL,
  `semana_idade` int(11) DEFAULT NULL,
  `aves_na_semana` int(11) DEFAULT NULL,
  `mort_d1` int(11) DEFAULT NULL,
  `mort_d2` int(11) DEFAULT NULL,
  `mort_d3` int(11) DEFAULT NULL,
  `mort_d4` int(11) DEFAULT NULL,
  `mort_d5` int(11) DEFAULT NULL,
  `mort_d6` int(11) DEFAULT NULL,
  `mort_d7` int(11) DEFAULT NULL,
  `mort_total` int(11) DEFAULT NULL,
  `data_pesagem` date DEFAULT NULL,
  `peso_medio` float DEFAULT NULL,
  `consumo_real_ave_dia` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lote_id` (`lote_id`),
  CONSTRAINT `producao_aves_ibfk_1` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producao_aves`
--

LOCK TABLES `producao_aves` WRITE;
/*!40000 ALTER TABLE `producao_aves` DISABLE KEYS */;
INSERT INTO `producao_aves` VALUES
(1,4,1,690,1,0,0,0,0,0,0,1,'2025-05-23',1.144,NULL);
/*!40000 ALTER TABLE `producao_aves` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `receitas_lote`
--

DROP TABLE IF EXISTS `receitas_lote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `receitas_lote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lote_id` int(11) NOT NULL,
  `data` date DEFAULT NULL,
  `tipo_receita` varchar(100) DEFAULT NULL,
  `descricao` text DEFAULT NULL,
  `valor` float NOT NULL,
  PRIMARY KEY (`id`),
  KEY `lote_id` (`lote_id`),
  CONSTRAINT `receitas_lote_ibfk_1` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receitas_lote`
--

LOCK TABLES `receitas_lote` WRITE;
/*!40000 ALTER TABLE `receitas_lote` DISABLE KEYS */;
/*!40000 ALTER TABLE `receitas_lote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tratamentos`
--

DROP TABLE IF EXISTS `tratamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tratamentos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lote_id` int(11) NOT NULL,
  `medicacao` varchar(100) DEFAULT NULL,
  `data_inicio` date DEFAULT NULL,
  `data_termino` date DEFAULT NULL,
  `periodo_carencia_dias` int(11) DEFAULT NULL,
  `forma_admin` varchar(50) DEFAULT NULL,
  `motivacao` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lote_id` (`lote_id`),
  CONSTRAINT `tratamentos_ibfk_1` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tratamentos`
--

LOCK TABLES `tratamentos` WRITE;
/*!40000 ALTER TABLE `tratamentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `tratamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(80) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES
(1,'jefferson.silva','scrypt:32768:8:1$D4MxKA58SYjz5kjD$768d62b67455f3f739a900024b9299eab20c57a7194f8b63f102194ceca1ff4b02d737f166a4120d206577693e985499d43cd522ba7ff5285fcfb57ff7133faa'),
(2,'rosilene.duarte','scrypt:32768:8:1$pKfq7F8BR4vjCWJA$efd2f0e3819e946d73621d6eeec39a9d39100380dcff3b850368e3318fa7358823a954eedaa525e9d3ff36b8fba3076f7fd2031d3119737accbf44bce8e93e23');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-11 19:35:30
