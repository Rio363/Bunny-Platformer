# Art from www.Kenney.nl
# Music from opengameart.org happy/yippee
# Some sounds from mixkit.com

from sprites import *
import random
import time

class Game():
	def __init__(self):
		pg.init()
		pg.mixer.init()
		self.screen = pg.display.set_mode((WIDTH, HEIGHT))
		pg.display.set_caption(TITLE)
		self.clock = pg.time.Clock()
		self.font_name = pg.font.match_font(FONT_NAME)

		self.running = True
		self.load_data()
		pg.display.set_icon(self.ICON)

	def load_data(self):
		self.score_data = shelve.open("data")
		self.score_data.setdefault("best_score", 0)

		img_dir = path.join(path.dirname(__file__), "img")
		self.snd_dir = path.join(path.dirname(__file__), "snds")

		# images...
		self.sprite_sheet = SpriteSheet(path.join(img_dir, SPRITESHEET_NAME))

		# Game HUD....
		self.ICON = self.bunny_mini = self.sprite_sheet.get_sprite(868, 1936, 52, 71)
		self.bunny_x = pg.image.load(path.join(img_dir, "numeralx.png")).convert()
		self.nums_lst = [pg.image.load(path.join(img_dir, "nums", img)).convert() for img in [f"numeral{n}.png" for n in range(10)]]
		[img.set_colorkey(BLACK) for img in self.nums_lst + [self.bunny_x]]

		self.gold_coin_mini = self.sprite_sheet.get_sprite(244, 1981, 61, 61)
		self.silver_coin_mini = self.sprite_sheet.get_sprite(307, 1981, 61, 61)
		self.bronze_coin_mini = self.sprite_sheet.get_sprite(329, 1390, 60, 61)
		self.carrot_mini = self.sprite_sheet.get_sprite(812, 554, 54, 49)
		self.bunny_hurt = self.sprite_sheet.get_sprite(382, 946, 150, 174)

		self.cloud_images = [pg.image.load(path.join(img_dir, img)) for img in [f"cloud{n + 1}.png" for n in range(3)]]

		# Sounds
		self.jump_sound = self.load_sound("Jump.wav", 0.15)
		self.pow_sound = self.load_sound("jump_power_up.wav", 0.2)
		self.life_pow_sound = self.load_sound("life.wav", 0.3)
		self.coin_sound = self.load_sound("coin_collect2.wav", 0.2)
		self.crunch_sound = self.load_sound("crunch.wav")
		self.lightning_sound = self.load_sound("lightning.wav")
		self.player_hit_sound = self.load_sound("player_hit.wav")
		self.spike_bullet_sound = self.load_sound("spike_bullet.wav")
		self.heli_sound = self.load_sound("Heli_sound.wav")
		self.lose_sound = self.load_sound("lose.wav")

	def load_sound(self, snd_name, vol=1):
		snd = pg.mixer.Sound(path.join(self.snd_dir, snd_name))
		snd.set_volume(vol)
		return snd

	def new(self):
		self.score = 0
		self.highest_score = self.score_data["best_score"]
		self.all_sprites = pg.sprite.LayeredUpdates()
		self.mobs = pg.sprite.Group()
		self.platforms = pg.sprite.Group()
		self.powerups = pg.sprite.Group()
		self.collectables = pg.sprite.Group()
		self.mobs_bullets = pg.sprite.Group()
		self.clouds = pg.sprite.Group()
		self.bunny = Bunny(self)

		for p in initial_platforms:
			Platform(self, *p)

		initial_clouds = [
			(random.randint(-50, WIDTH - 50), random.randint(0, HEIGHT - 100)),
			(random.randint(-50, WIDTH - 50), random.randint(0, HEIGHT - 100)),
			(random.randint(-50, WIDTH - 50), random.randint(0, HEIGHT - 100)),
			(random.randint(-50, WIDTH - 50), random.randint(0, HEIGHT - 100)),
		]

		for c in initial_clouds:
			Cloud(self, *c)

		self.run()

	def run(self):
		pg.mixer.music.load(path.join(self.snd_dir, "happy.wav"))
		pg.mixer.music.set_volume(0.5)
		pg.mixer.music.play(loops=-1)
		self.playing = True

		while self.playing:
			self.clock.tick(FPS)
			self.update()
		
		pg.mixer.music.fadeout(500)

	def events(self):
		for event in pg.event.get():
			if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
				self.playing = False
				self.running = False
			if event.type == pg.KEYDOWN:
				if event.key == pg.K_SPACE:
					self.bunny.jump()
			if event.type == pg.KEYUP:
				if event.key == pg.K_SPACE:
					self.bunny.jump_cut()
				if event.key == pg.K_a:
					self.score += 1000

	def update(self):
		self.events()
		self.all_sprites.update()
		self.draw()
		self.stand_on_platform()
		self.screen_scroller()
		self.collision_manager()

		# Check if Bunny fell over...
		if self.bunny.pos.y > HEIGHT:
			for p in self.platforms:
				p.rect.y -= abs(self.bunny.vel.y)
				if p.rect.bottom < 0:
					p.kill()
			for pow in self.powerups:
				pow.rect.y -= abs(self.bunny.vel.y)
			for mob in self.mobs:
				mob.rect.y -= abs(self.bunny.vel.y)
			for mob_bullet in self.mobs_bullets:
				mob_bullet.rect.y -= abs(self.bunny.vel.y)
			for cloud in self.clouds:
				cloud.rect.y -= abs(self.bunny.vel.y) / 3.2

		if len(self.platforms) == 0:
			self.bunny.lives = 0

		if self.bunny.lives <= 0:
			self.lose_sound.play()
			time.sleep(1)
			self.playing = False

	def collision_manager(self):
		self.collect_powerups()
		self.collect_assets()
		self.mob_collider() # Mob/Mob_bullet collisions

	def collect_powerups(self):
		hits = pg.sprite.spritecollide(self.bunny, self.powerups, True)
		if hits:
			hit = hits[0]
			if hit.pow_type == "boost":
				self.bunny.pow_jumping = True
				self.bunny.vel.y = POW_JUMP_HEIGHT
				self.pow_sound.play()
			elif hit.pow_type == "life":
				self.bunny.lives += 1
				self.life_pow_sound.play()

	def collect_assets(self):
		hits = pg.sprite.spritecollide(self.bunny, self.collectables, True)
		if hits:
			hit = hits[0]
			if hit.collectable_type in ["gold_coin", "silver_coin", "bronze_coin"]:
				self.coin_sound.play()

				if hit.collectable_type == "gold_coin":
					self.bunny.gold_coins += 1
				elif hit.collectable_type == "silver_coin":
					self.bunny.silver_coins += 1
				elif hit.collectable_type == "bronze_coin":
					self.bunny.bronze_coins += 1

			if hit.collectable_type == "carrot":
				self.crunch_sound.play()
				self.bunny.carrots += 1
	
	def mob_collider(self):
		if not self.bunny.hurt:
			hits = pg.sprite.spritecollide(self.bunny, self.mobs, True, pg.sprite.collide_mask)
			if hits:
				self.bunny.hurt_bunny()
				self.player_hit_sound.play()
				# hit = hits[0]
				# if hit.mob_type == "flyman":
				# 	print("FLYMAN")
				# elif hit.mob_type == "wingman":
				# 	print("WINGMAN")
				# elif hit.mob_type == "spikeman":
				# 	print("SPIKEMAN")

				self.bunny.lives -= 1

			hits = pg.sprite.spritecollide(self.bunny, self.mobs_bullets, True)
			if hits:
				self.bunny.hurt_bunny()
				self.player_hit_sound.play()	
				for hit in hits:
					self.bunny.lives -= 1

	def screen_scroller(self):
		if not self.bunny.hurt:
			if self.bunny.rect.top < HEIGHT / 4:
				self.bunny.pos.y += max(5, abs(self.bunny.vel.y))
				for p in self.platforms:
					p.rect.y += max(5, abs(self.bunny.vel.y))

					if p.rect.top > HEIGHT + 20:
						p.kill()
						self.score += 10

				for mob in self.mobs:
					mob.rect.y += max(5, abs(self.bunny.vel.y))
					if mob.rect.top > HEIGHT:
						mob.kill()

				for b in self.mobs_bullets:
					b.rect.y += max(5, abs(self.bunny.vel.y))

				for c in self.clouds:
					c.rect.y += max(2, abs(self.bunny.vel.y) / 3)

		while len(self.platforms) < ON_SCREEN_PLATFORMS_COUNT:
			self.add_platform()
		while len(self.clouds) < CLOUDS_COUNT:
			Cloud(self)

	def stand_on_platform(self):
		if self.bunny.vel.y > 0: # Land only when desending..
			hits = pg.sprite.spritecollide(self.bunny, self.platforms, False)
			# Stand only if:
			# Bunny's bottom is higher than platform's bottom
			# platform's bottom is lowest in hits
			# bunny's X is between platform's width
			if hits:
				lowest_platform = hits[0]
				for hit in hits:
					if hit.rect.bottom > lowest_platform.rect.bottom:
						lowest_platform = hit 

				if self.bunny.pos.x > lowest_platform.rect.left - 10 and self.bunny.pos.x < lowest_platform.rect.right + 10:
					if self.bunny.pos.y < lowest_platform.rect.bottom - lowest_platform.rect.height / 3:
						self.bunny.pos.y = lowest_platform.rect.top
						self.bunny.vel.y = 0
						self.bunny.jumping = False
						self.bunny.pow_jumping = False

	def add_platform(self):
		w = random.randint(60, 200)
		h = 25
		x = random.randint(0, WIDTH - w)
		y = random.randint(-25, -15)
		Platform(self, x, y)

	def draw(self):
		self.screen.fill(LIGHT_BLUE)
		self.all_sprites.draw(self.screen)
		self.draw_HUD()
		pg.display.flip()

	def draw_HUD(self):
		# self.draw_text(self.score, WIDTH / 2, 30, 30)
		if len(str(self.score)) == 1:
			self.draw_numbers(self.score, WIDTH / 2 , 20)
		else:
			self.draw_numbers(self.score, WIDTH / 2 - (10 * len(str(self.score)) - 1), 20) # HERE

		self.mini_assets()

	def draw_text(self, txt, x, y, size=22):
		font = pg.font.Font(self.font_name, size)
		txt_surf = font.render(str(txt), True, WHITE)
		txt_rect = txt_surf.get_rect(center=[x, y])
		self.screen.blit(txt_surf, txt_rect)

	def draw_numbers(self, value, starting_x, y):
		distance = 0
		for num in range(len(str(value))):
			self.screen.blit(self.nums_lst[int(str(value)[num])], (starting_x + distance, y))
			distance += 20

	def mini_assets(self):
		# Lives
		self.screen.blit(self.bunny_mini, (WIDTH - self.bunny_mini.get_rect().width - 50, 10))
		self.screen.blit(self.bunny_x, (WIDTH - 46, 20))
		self.draw_numbers(self.bunny.lives, WIDTH - 25, 19)
		# Gold Coins...
		self.screen.blit(self.gold_coin_mini, (WIDTH - self.gold_coin_mini.get_rect().width - 65, 50))
		self.screen.blit(self.bunny_x, (WIDTH - 63, 57))
		self.draw_numbers(self.bunny.gold_coins, WIDTH - 45, 57)
		# Silver Coins...
		self.screen.blit(self.silver_coin_mini, (10, 10))
		self.screen.blit(self.bunny_x, (43, 20))
		self.draw_numbers(self.bunny.silver_coins,  65, 19)
		# Bronze Coins...
		self.screen.blit(self.bronze_coin_mini, (10, 50))
		self.screen.blit(self.bunny_x, (43, 57))
		self.draw_numbers(self.bunny.bronze_coins,  65, 57)
		# Carrot...
		self.screen.blit(self.carrot_mini, (WIDTH / 2 - 30, 52))
		self.screen.blit(self.bunny_x, (WIDTH / 2, 57))
		self.draw_numbers(self.bunny.carrots,  WIDTH / 2 + 20, 57)

	def show_splash_screen(self):
		bunny_jump = self.sprite_sheet.get_sprite(382, 763, 150, 181)
		bunny_jump_rect = bunny_jump.get_rect(center=[WIDTH/2, HEIGHT/2 + 70])

		self.screen.fill(LIGHT_BLUE)
		self.draw_text("Bunny!", WIDTH / 2, HEIGHT / 4 - 20, 60)
		if self.score_data['best_score'] > 0:
			self.draw_text(f"Highest score: {self.score_data['best_score']}", WIDTH / 2, HEIGHT / 4 + 40, 20)
		self.draw_text("Arrows to move, space to jump", WIDTH / 2, HEIGHT / 2 - 20)
		self.screen.blit(bunny_jump, bunny_jump_rect)
		self.draw_text("Press Enter to start game...", WIDTH / 2, HEIGHT - HEIGHT / 4, 25)
		pg.display.flip()
		self.wait_key_press()

	def show_game_over_screen(self):
		bunny_hurt = self.bunny_hurt
		bunny_hurt_rect = bunny_hurt.get_rect(center=[WIDTH/2, HEIGHT/2 + 60])

		self.screen.fill(LIGHT_BLUE)
		self.draw_text("Game Over", WIDTH / 2, HEIGHT / 2 - 60, 55)
		self.draw_text(f"Score: {self.score}", WIDTH / 2, 30)
		if self.score > self.highest_score:
			self.score_data["best_score"] = self.score
			self.draw_text(f"new high score!".upper(), WIDTH / 2, 60)
		else:
			self.draw_text(f"Highest score: {self.highest_score}", WIDTH / 2, 60)
		self.screen.blit(bunny_hurt, bunny_hurt_rect)

		self.draw_text("Press Enter to play again", WIDTH / 2, HEIGHT - HEIGHT / 4, 25)
		pg.display.flip()
		self.wait_key_press()

	def wait_key_press(self):
		pg.mixer.music.load(path.join(self.snd_dir, "Yippee.wav"))
		pg.mixer.music.set_volume(0.3)
		pg.mixer.music.play()

		self.waiting = True
		while self.waiting:
			self.clock.tick(FPS)
			for event in pg.event.get():
					if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
						self.waiting = self.running = False
					if event.type == pg.KEYUP and event.key == pg.K_RETURN:
						self.waiting = False

		pg.mixer.music.fadeout(500)



g = Game()
g.show_splash_screen()

while g.running:
	g.new()
	if g.running:
		g.show_game_over_screen()


# Invencible for some time after hitting a mob/attack
