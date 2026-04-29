<?php
require_once 'config.php';
requireLogin();
$db = getDB();

$animeId = intval($_GET['id'] ?? 0);
if (!$animeId) { header('Location: home.php'); exit; }

$stmt = $db->prepare("SELECT a.*, c.name as cat_name, c.color as cat_color FROM animes a LEFT JOIN categories c ON a.category_id = c.id WHERE a.id = ?");
$stmt->bind_param("i", $animeId);
$stmt->execute();
$anime = $stmt->get_result()->fetch_assoc();
if (!$anime) { header('Location: home.php'); exit; }

// Episodes with user progress
$uid = $_SESSION['user_id'];
$stmt2 = $db->prepare("SELECT e.*, wp.progress_seconds, wp.completed FROM episodes e LEFT JOIN watch_progress wp ON e.id=wp.episode_id AND wp.user_id=? WHERE e.anime_id=? ORDER BY e.episode_number");
$stmt2->bind_param("ii", $uid, $animeId);
$stmt2->execute();
$episodes = $stmt2->get_result()->fetch_all(MYSQLI_ASSOC);

// Is saved?
$stmt3 = $db->prepare("SELECT id FROM saved_animes WHERE user_id=? AND anime_id=?");
$stmt3->bind_param("ii", $uid, $animeId);
$stmt3->execute();
$isSaved = $stmt3->get_result()->num_rows > 0;

// Increment views
$db->query("UPDATE animes SET views=views+1 WHERE id=$animeId");

// Related
$related = $db->query("SELECT * FROM animes WHERE category_id={$anime['category_id']} AND id!=$animeId ORDER BY RAND() LIMIT 6")->fetch_all(MYSQLI_ASSOC);
$db->close();

// First unwatched episode
$firstEp = null; $continueEp = null;
foreach($episodes as $ep) {
    if (!$firstEp) $firstEp = $ep;
    if ($ep['progress_seconds'] > 0 && !$ep['completed'] && !$continueEp) $continueEp = $ep;
}
$watchEp = $continueEp ?: $firstEp;
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><?= htmlspecialchars($anime['title']) ?> — AniStream</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
:root{--bg:#020208;--surface:rgba(13,13,26,0.9);--card:rgba(16,16,32,0.85);--cyan:#00d4ff;--purple:#7c3aed;--pink:#ff2d78;--text:#f0f0ff;--secondary:#8888aa;--muted:#44445a;--border:rgba(255,255,255,0.06);--radius:14px;}
*{margin:0;padding:0;box-sizing:border-box;}
::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-thumb{background:rgba(0,212,255,0.3);}
body{font-family:'Rajdhani',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;}

.top-bar{display:flex;align-items:center;gap:16px;padding:14px 28px;background:rgba(8,8,16,0.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:50;}
.back-btn{display:flex;align-items:center;gap:8px;color:var(--secondary);text-decoration:none;font-size:13px;font-weight:600;transition:color 0.2s;}
.back-btn:hover{color:var(--cyan);}
.logo-home{font-family:'Orbitron',sans-serif;font-size:16px;font-weight:900;text-decoration:none;background:linear-gradient(135deg,#fff,var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}

/* Hero */
.hero{position:relative;height:500px;overflow:hidden;}
.hero-bg-img{position:absolute;inset:0;background-size:cover;background-position:center;filter:brightness(0.35) saturate(1.3);transform:scale(1.05);}
.hero-gradient{position:absolute;inset:0;background:linear-gradient(to right,rgba(2,2,8,0.95) 40%,transparent 80%),linear-gradient(to top,rgba(2,2,8,1) 0%,transparent 40%);}
.hero-content{position:absolute;bottom:0;left:0;padding:48px;display:flex;gap:32px;align-items:flex-end;max-width:900px;}
.hero-poster{
  width:160px;height:230px;border-radius:12px;object-fit:cover;flex-shrink:0;
  box-shadow:0 20px 50px rgba(0,0,0,0.8),0 0 0 1px rgba(255,255,255,0.1);
}
.hero-info{flex:1;}
.hero-cat{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;background:rgba(0,212,255,0.12);border:1px solid rgba(0,212,255,0.3);color:var(--cyan);}
.hero-title{font-family:'Orbitron',sans-serif;font-size:34px;font-weight:900;line-height:1.1;margin-bottom:10px;}
.hero-meta{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:16px;}
.meta-item{display:flex;align-items:center;gap:5px;font-size:13px;color:var(--secondary);}
.meta-item.rating{color:#ffd700;}
.hero-desc{color:var(--secondary);font-size:14px;line-height:1.6;margin-bottom:20px;max-width:600px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.hero-btns{display:flex;gap:10px;flex-wrap:wrap;}
.btn-watch{display:flex;align-items:center;gap:8px;padding:12px 24px;border-radius:50px;background:var(--cyan);color:#000;font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase;text-decoration:none;transition:all 0.3s;border:none;cursor:pointer;}
.btn-watch:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,212,255,0.4);}
.btn-save{display:flex;align-items:center;gap:8px;padding:12px 20px;border-radius:50px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);color:var(--text);font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;cursor:pointer;transition:all 0.3s;letter-spacing:0.5px;}
.btn-save.saved{border-color:rgba(255,45,120,0.4);color:var(--pink);}
.btn-save:hover{background:rgba(255,255,255,0.1);}

/* Main layout */
.main{padding:40px 48px;display:grid;grid-template-columns:1fr 320px;gap:32px;}
@media(max-width:900px){.main{grid-template-columns:1fr;padding:20px;}.hero-content{flex-direction:column;gap:16px;padding:20px;}.hero-poster{width:100px;height:145px;}.hero-title{font-size:22px;}}

/* Episodes */
.section-title{font-family:'Orbitron',sans-serif;font-size:14px;font-weight:700;letter-spacing:1px;margin-bottom:16px;display:flex;align-items:center;gap:10px;}
.section-title::before{content:'';width:3px;height:18px;background:linear-gradient(to bottom,var(--cyan),var(--purple));border-radius:2px;}

.ep-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;}
.ep-card{
  display:flex;align-items:center;gap:14px;padding:14px;
  background:var(--card);border:1px solid var(--border);border-radius:12px;
  cursor:pointer;transition:all 0.25s;text-decoration:none;color:inherit;position:relative;overflow:hidden;
}
.ep-card:hover{border-color:rgba(0,212,255,0.2);transform:translateX(4px);}
.ep-card.watching{border-color:rgba(0,212,255,0.2);background:rgba(0,212,255,0.04);}
.ep-card.done{opacity:0.6;}
.ep-num-box{
  width:44px;height:44px;border-radius:10px;flex-shrink:0;
  background:rgba(255,255,255,0.04);border:1px solid var(--border);
  display:flex;align-items:center;justify-content:center;
  font-family:'Orbitron',sans-serif;font-size:14px;font-weight:700;color:var(--secondary);
}
.ep-card.watching .ep-num-box,.ep-card:hover .ep-num-box{background:var(--cyan);color:#000;border-color:transparent;box-shadow:0 0 12px rgba(0,212,255,0.3);}
.ep-info{flex:1;min-width:0;}
.ep-title{font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:4px;}
.ep-meta{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--muted);}
.ep-prog{position:absolute;bottom:0;left:0;right:0;height:2px;background:rgba(255,255,255,0.04);}
.ep-prog-fill{height:100%;background:var(--cyan);box-shadow:0 0 4px var(--cyan);}
.ep-check{color:var(--cyan);font-size:12px;}

/* Related */
.related-grid{display:flex;flex-direction:column;gap:10px;}
.related-item{display:flex;gap:10px;padding:10px;background:var(--card);border:1px solid var(--border);border-radius:10px;text-decoration:none;color:inherit;transition:all 0.2s;}
.related-item:hover{border-color:rgba(0,212,255,0.2);transform:translateX(2px);}
.related-poster{width:46px;height:64px;border-radius:6px;object-fit:cover;flex-shrink:0;background:#111;}
.related-info{flex:1;min-width:0;}
.related-title{font-size:12px;font-weight:700;line-height:1.3;margin-bottom:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.related-meta{font-size:10px;color:var(--muted);display:flex;gap:6px;}
</style>
</head>
<body>

<div class="top-bar">
  <a href="home.php" class="back-btn"><i class="fas fa-arrow-left"></i> Back</a>
  <a href="home.php" class="logo-home">ANISTREAM</a>
</div>

<!-- HERO -->
<div class="hero">
  <div class="hero-bg-img" style="background-image:url('<?= htmlspecialchars($anime['cover_image']) ?>')"></div>
  <div class="hero-gradient"></div>
  <div class="hero-content">
    <img class="hero-poster" src="<?= htmlspecialchars($anime['cover_image'] ?: 'https://via.placeholder.com/160x230/111/333') ?>" alt="">
    <div class="hero-info">
      <?php if($anime['cat_name']): ?>
      <div class="hero-cat" style="border-color:<?= htmlspecialchars($anime['cat_color']??'var(--cyan)') ?>33;color:<?= htmlspecialchars($anime['cat_color']??'var(--cyan)') ?>">
        <?= htmlspecialchars($anime['cat_name']) ?>
      </div>
      <?php endif; ?>
      <h1 class="hero-title"><?= htmlspecialchars($anime['title']) ?></h1>
      <div class="hero-meta">
        <span class="meta-item rating"><i class="fas fa-star"></i> <?= $anime['rating'] ?>/10</span>
        <span class="meta-item"><i class="fas fa-tv"></i> <?= $anime['episodes_count'] ?> Episodes</span>
        <?php if($anime['year']): ?><span class="meta-item"><i class="fas fa-calendar"></i> <?= $anime['year'] ?></span><?php endif; ?>
        <?php if($anime['studio']): ?><span class="meta-item"><i class="fas fa-building"></i> <?= htmlspecialchars($anime['studio']) ?></span><?php endif; ?>
        <span class="meta-item"><i class="fas fa-eye"></i> <?= number_format($anime['views']) ?> views</span>
        <span class="meta-item"><span style="padding:2px 8px;border-radius:4px;background:rgba(0,212,255,0.1);font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--cyan)"><?= ucfirst($anime['status']) ?></span></span>
      </div>
      <p class="hero-desc"><?= htmlspecialchars($anime['description']) ?></p>
      <div class="hero-btns">
        <?php if($watchEp): ?>
        <a href="watch.php?episode=<?= $watchEp['id'] ?>" class="btn-watch">
          <i class="fas fa-play"></i>
          <?= $continueEp ? 'Continue Ep '.$continueEp['episode_number'] : 'Watch Now' ?>
        </a>
        <?php endif; ?>
        <button class="btn-save <?= $isSaved?'saved':'' ?>" id="saveBtn" onclick="toggleSave(<?= $animeId ?>, this)">
          <i class="fas fa-bookmark"></i> <?= $isSaved ? 'Saved' : 'Save' ?>
        </button>
      </div>
    </div>
  </div>
</div>

<!-- MAIN -->
<div class="main">
  <div>
    <div class="section-title">Episodes (<?= count($episodes) ?>)</div>
    <?php if(empty($episodes)): ?>
    <p style="color:var(--muted);font-size:14px">No episodes added yet.</p>
    <?php else: ?>
    <div class="ep-grid">
      <?php foreach($episodes as $ep):
        $pct = ($ep['duration']>0 && $ep['progress_seconds']>0) ? min(100,($ep['progress_seconds']/$ep['duration'])*100) : 0;
        $cls = $ep['completed'] ? 'done' : ($ep['progress_seconds']>0 ? 'watching' : '');
      ?>
      <a href="watch.php?episode=<?= $ep['id'] ?>" class="ep-card <?= $cls ?>">
        <div class="ep-num-box"><?= $ep['episode_number'] ?></div>
        <div class="ep-info">
          <div class="ep-title"><?= htmlspecialchars($ep['title'] ?: 'Episode '.$ep['episode_number']) ?></div>
          <div class="ep-meta">
            <?php if($ep['duration']): ?><span><i class="fas fa-clock"></i> <?= floor($ep['duration']/60) ?>m</span><?php endif; ?>
            <?php if($ep['completed']): ?><span class="ep-check"><i class="fas fa-check-circle"></i> Watched</span><?php elseif($ep['progress_seconds']>0): ?><span style="color:var(--cyan)"><i class="fas fa-play"></i> <?= round($pct) ?>%</span><?php endif; ?>
          </div>
        </div>
        <?php if($pct > 0): ?>
        <div class="ep-prog"><div class="ep-prog-fill" style="width:<?= $pct ?>%"></div></div>
        <?php endif; ?>
      </a>
      <?php endforeach; ?>
    </div>
    <?php endif; ?>
  </div>

  <!-- SIDEBAR -->
  <div>
    <?php if(!empty($related)): ?>
    <div class="section-title">Related Anime</div>
    <div class="related-grid">
      <?php foreach($related as $r): ?>
      <a href="anime.php?id=<?= $r['id'] ?>" class="related-item">
        <img class="related-poster" src="<?= htmlspecialchars($r['cover_image']?:'') ?>" alt="">
        <div class="related-info">
          <div class="related-title"><?= htmlspecialchars($r['title']) ?></div>
          <div class="related-meta">
            <span><i class="fas fa-star" style="color:#ffd700"></i> <?= $r['rating'] ?></span>
            <span><?= $r['episodes_count'] ?> eps</span>
          </div>
        </div>
      </a>
      <?php endforeach; ?>
    </div>
    <?php endif; ?>
  </div>
</div>

<script>
async function toggleSave(animeId, btn) {
  const res = await fetch('api/save.php', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({anime_id:animeId})});
  const data = await res.json();
  btn.classList.toggle('saved', data.saved);
  btn.innerHTML = `<i class="fas fa-bookmark"></i> ${data.saved ? 'Saved' : 'Save'}`;
}
</script>
</body>
</html>