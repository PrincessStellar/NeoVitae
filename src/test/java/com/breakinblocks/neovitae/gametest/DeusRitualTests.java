package com.breakinblocks.neovitae.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.phys.AABB;
import com.breakinblocks.neovitae.api.soul.AnimaTicket;
import com.breakinblocks.neovitae.common.datacomponent.Anima;
import com.breakinblocks.neovitae.common.entity.projectile.EntityMeteor;
import com.breakinblocks.neovitae.common.item.ItemRitualDiviner;
import com.breakinblocks.neovitae.common.item.NVItems;
import com.breakinblocks.neovitae.common.meteor.MeteorLayer;
import com.breakinblocks.neovitae.common.recipe.meteor.MeteorRecipe;
import com.breakinblocks.neovitae.common.recipe.meteor.MeteorRecipeHelper;
import com.breakinblocks.neovitae.gametest.base.NVTestRegistrar;
import com.breakinblocks.neovitae.ritual.EnumRuneType;
import com.breakinblocks.neovitae.ritual.Ritual;
import com.breakinblocks.neovitae.ritual.RitualComponent;
import com.breakinblocks.neovitae.ritual.RitualRegistry;
import com.breakinblocks.neovitae.util.helper.AnimaHelper;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public final class DeusRitualTests {

    private static final Map<String, String> DEUS_TO_BASE = Map.of(
            "deus_well_of_suffering", "well_of_suffering",
            "deus_torment_nexus", "torment_nexus",
            "deus_magnetism", "magnetism",
            "deus_crystallum_fractura", "crystallum_fractura",
            "deus_green_grove", "green_grove",
            "deus_placer", "placer",
            "deus_felling", "felling",
            "deus_meteor", "meteor",
            "deus_armour_evolve", "armour_evolve");

    private static final UUID OWNER = UUID.fromString("5d1e8b2a-93c4-4f7e-a6b1-0e2f4c8d9a37");

    private DeusRitualTests() {}

    public static void register(NVTestRegistrar r) {
        r.add("deus/layouts_add_a_crown_of_deus_stones", 20, helper -> {
            for (Map.Entry<String, String> pair : DEUS_TO_BASE.entrySet()) {
                Ritual deus = RitualRegistry.getRitual(pair.getKey());
                Ritual base = RitualRegistry.getRitual(pair.getValue());
                if (deus == null || base == null) {
                    helper.fail("Missing ritual " + pair.getKey() + " or " + pair.getValue());
                    return;
                }
                List<RitualComponent> deusLayout = layout(deus);
                List<RitualComponent> baseLayout = layout(base);
                if (!deusLayout.containsAll(baseLayout)) {
                    helper.fail(pair.getKey() + " should contain every stone of " + pair.getValue());
                    return;
                }
                long deusStones = deusLayout.stream().filter(c -> c.runeType() == EnumRuneType.DEUS).count();
                if (deusStones != 16 || deusLayout.size() != baseLayout.size() + 16) {
                    helper.fail(pair.getKey() + " should add exactly 16 Deus stones, has " + deusStones
                            + " of " + deusLayout.size() + " total vs " + baseLayout.size());
                    return;
                }
            }
            helper.succeed();
        });

        r.add("deus/rituals_need_divinus_crystal", 20, helper -> {
            for (String name : DEUS_TO_BASE.keySet()) {
                Ritual deus = RitualRegistry.getRitual(name);
                if (deus.getCrystalLevel() != 2) {
                    helper.fail(name + " should need crystal level 2, needs " + deus.getCrystalLevel());
                    return;
                }
            }
            helper.succeed();
        });

        r.add("deus/only_deus_diviner_places_deus_stones", 20, helper -> {
            ItemStack tenebrae = new ItemStack(NVItems.RITUAL_DIVINER_TENEBRAE.get());
            ItemStack deus = new ItemStack(NVItems.RITUAL_DIVINER_DEUS.get());
            boolean tenebraeCan = ((ItemRitualDiviner) tenebrae.getItem()).canPlaceRitualStone(EnumRuneType.DEUS, tenebrae);
            boolean deusCan = ((ItemRitualDiviner) deus.getItem()).canPlaceRitualStone(EnumRuneType.DEUS, deus);
            helper.assertTrue(!tenebraeCan, "The Tenebrae diviner should not place Deus stones");
            helper.assertTrue(deusCan, "The Deus diviner should place Deus stones");
            helper.succeed();
        });

        r.addIsolated("deus/nether_star_meteor_is_all_ore", 100, DeusRitualTests::deusMeteorNetherStarIsAllOre);

        r.add("deus/ores_only_meteor_layer_has_no_filler", 40, helper -> {
            BlockPos center = new BlockPos(2, 2, 2);
            MeteorLayer layer = new MeteorLayer(2, 0, Blocks.COBBLESTONE)
                    .addWeightedBlock(Blocks.DIAMOND_ORE, 100)
                    .addWeightedBlock(Blocks.CRYING_OBSIDIAN, 100)
                    .addWeightedBlock(Blocks.GLOWSTONE, 100)
                    .setMinWeight(1000);
            List<BlockPos> open = new ArrayList<>();
            for (BlockPos rel : BlockPos.betweenClosed(center.offset(-2, -2, -2), center.offset(2, 2, 2))) {
                BlockPos offset = rel.subtract(center);
                if (layer.checkIfSphere(2, offset.getX(), offset.getY(), offset.getZ()) && helper.getBlockState(rel).isAir()) {
                    open.add(rel.immutable());
                }
            }
            layer.buildLayer(helper.getLevel(), helper.absolutePos(center), -1, true);

            int ores = 0;
            int glowstone = 0;
            for (BlockPos rel : open) {
                if (helper.getBlockState(rel).is(Blocks.DIAMOND_ORE)) {
                    ores++;
                } else if (helper.getBlockState(rel).is(Blocks.GLOWSTONE)) {
                    glowstone++;
                } else {
                    helper.fail("Ores-only meteor placed " + helper.getBlockState(rel) + " at " + rel);
                    return;
                }
            }
            helper.assertTrue(ores > 0 && glowstone > 0, "Ores-only meteor layer should place both ore and glowstone");
            helper.succeed();
        });
    }

    private static void deusMeteorNetherStarIsAllOre(GameTestHelper helper) {
        Anima anima = AnimaHelper.getAnima(OWNER);
        if (anima.getCurrentEV() < 5000000) {
            anima.add(AnimaTicket.create(10000000), 100000000);
        }
        BlockPos masterRel = new BlockPos(2, 1, 2);
        helper.setBlock(masterRel.above(), Blocks.CHEST);
        ChestBlockEntity chest = helper.getBlockEntity(masterRel.above(), ChestBlockEntity.class);
        chest.setItem(0, new ItemStack(Items.NETHER_STAR));

        BlockPos master = helper.absolutePos(masterRel);
        Ritual ritual = RitualRegistry.getRitual("deus_meteor").getNewCopy();
        ritual.performRitual(new QuarryThroughputTests.StubMaster(helper.getLevel(), master, OWNER));

        AABB column = new AABB(master.getX() - 1, helper.getLevel().getMinY(), master.getZ() - 1,
                master.getX() + 2, helper.getLevel().getMaxY() + 64, master.getZ() + 2);
        List<EntityMeteor> meteors = helper.getLevel().getEntitiesOfClass(EntityMeteor.class, column);
        if (meteors.size() != 1) {
            meteors.forEach(Entity::discard);
            helper.fail("Expected one meteor in flight, got " + meteors.size());
            return;
        }
        MeteorRecipe recipe = MeteorRecipeHelper.findRecipe(helper.getLevel(), new ItemStack(Items.NETHER_STAR));
        int targetY = master.getY() + 1 + recipe.getMaxRadius();
        EntityMeteor meteor = meteors.getFirst();
        meteor.setDeltaMovement(0, -0.1, 0);
        meteor.setPos(master.getX() + 0.5, targetY + 0.05, master.getZ() + 0.5);
        meteor.tick();
        if (meteor.isAlive()) {
            meteor.discard();
            helper.fail("Meteor did not detonate at its target height");
            return;
        }

        int radius = recipe.getMaxRadius();
        BlockPos center = new BlockPos(master.getX(), targetY, master.getZ());
        int filler = 0;
        int total = 0;
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-radius, -radius, -radius), center.offset(radius, radius, radius))) {
            var state = helper.getLevel().getBlockState(pos);
            if (state.isAir()) continue;
            total++;
            if (state.is(Blocks.NETHERRACK) || state.is(Blocks.CRYING_OBSIDIAN)) filler++;
        }
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-radius, -radius, -radius), center.offset(radius, radius, radius))) {
            if (pos.getY() > master.getY() + 1) helper.getLevel().removeBlock(pos, false);
        }
        if (filler > 0) {
            helper.fail("Deus nether star meteor placed " + filler + " netherrack or crying obsidian out of " + total + " blocks");
            return;
        }
        helper.succeed();
    }

    private static List<RitualComponent> layout(Ritual ritual) {
        List<RitualComponent> components = new ArrayList<>();
        ritual.gatherComponents(components::add);
        return components;
    }
}
