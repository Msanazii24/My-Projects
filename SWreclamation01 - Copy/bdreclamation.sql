-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : mar. 24 mars 2026 à 10:45
-- Version du serveur :  10.4.13-MariaDB
-- Version de PHP : 7.4.7

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `bdreclamation`
--

-- --------------------------------------------------------

CREATE OR REPLACE DATABASE bdreclamation;
USE bdreclamation;

--
-- Structure de la table `categorie`
--

CREATE TABLE `categorie` (
  `idcat` int(11) NOT NULL,
  `libelle` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `categorie`
--

INSERT INTO `categorie` (`idcat`, `libelle`) VALUES
(1, 'authentification'),
(2, 'branchement'),
(3, 'synchronisation'),
(4, 'autres');

-- --------------------------------------------------------

--
-- Structure de la table `client`
--

CREATE TABLE `client` (
  `telclt` varchar(8) NOT NULL,
  `nom` varchar(20) NOT NULL,
  `prenom` varchar(20) NOT NULL,
  `genre` varchar(1) NOT NULL,
  `adresse` varchar(50) NOT NULL,
  `email` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `client`
--

INSERT INTO `client` (`telclt`, `nom`, `prenom`, `genre`, `adresse`, `email`) VALUES
('76222111', 'mahari', 'tarek', 'H', 'doualy,gafsa', 'tarek@hotmail.com'),
('76426132', 'othmani', 'samia', 'F', 'el mahassen,tozeur', 'samia@gmail.com'),
('72123456', 'Mastouri', 'jihen', 'F', 'Mrezga, Nabeur', 'jihen@yahoo.fr'),
('70717171', 'Gafsa', 'Salah', 'H', 'Aouina, Tunis', 'Gafsi@gmail.com');

-- --------------------------------------------------------

--
-- Structure de la table `reclamation`
--

CREATE TABLE `reclamation` (
  `numrec` int(11) NOT NULL,
  `description` varchar(50) NOT NULL,
  `etat` varchar(1) NOT NULL,
  `daterec` datetime NOT NULL,
  `daterep` date NOT NULL,
  `telclt` varchar(8) NOT NULL,
  `idcat` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `reclamation`
--

INSERT INTO `reclamation` (`numrec`, `description`, `etat`, `daterec`, `daterep`, `telclt`, `idcat`) VALUES
(1, 'pas de tonalité', 'N', '2026-03-24 10:43:21', '1970-01-01', '76222111', 3),
(2, 'pas de connexion', 'N', '2026-03-05 00:00:00', '1970-01-01', '76426132', 1);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `categorie`
--
ALTER TABLE `categorie`
  ADD PRIMARY KEY (`idcat`);

--
-- Index pour la table `client`
--
ALTER TABLE `client`
  ADD PRIMARY KEY (`telclt`);

--
-- Index pour la table `reclamation`
--
ALTER TABLE `reclamation`
  ADD PRIMARY KEY (`numrec`),
  ADD KEY `telclt` (`telclt`),
  ADD KEY `idcat` (`idcat`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `reclamation`
--
ALTER TABLE `reclamation`
  MODIFY `numrec` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `reclamation`
--
ALTER TABLE `reclamation`
  ADD CONSTRAINT `reclamation_ibfk_1` FOREIGN KEY (`telclt`) REFERENCES `client` (`telclt`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `reclamation_ibfk_2` FOREIGN KEY (`idcat`) REFERENCES `categorie` (`idcat`) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE Client 
  ADD CONSTRAINT CK1 CHECK (genre IN ('H','F'));
ALTER TABLE Reclamation 
  ADD CONSTRAINT CK2 CHECK (Etat IN ('O','N'));

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
