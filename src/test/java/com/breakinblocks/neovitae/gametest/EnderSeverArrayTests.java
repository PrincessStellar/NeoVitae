package com.breakinblocks.neovitae.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.EnderMan;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityTeleportEvent;
import com.breakinblocks.neovitae.common.alchemyarray.AlchemyArrayEffectEnderSever;
import com.breakinblocks.neovitae.common.block.NVBlocks;
import com.breakinblocks.neovitae.common.blockentity.AlchemyArrayBlockEntity;
import com.breakinblocks.neovitae.common.item.NVItems;
import com.breakinblocks.neovitae.gametest.base.NVTestRegistrar;

public final class EnderSeverArrayTests {

    private EnderSeverArrayTests() {}

    private static final BlockPos ARRAY_POS = new BlockPos(2, 1, 2);

    public static void register(NVTestRegistrar r) {
        r.add("ender_sever_array/blocks_ender_teleports_in_range", 40, EnderSeverArrayTests::blocksEnderTeleportsInRange);
    }

    private static void blocksEnderTeleportsInRange(GameTestHelper helper) {
        helper.setBlock(ARRAY_POS, NVBlocks.ALCHEMY_ARRAY.get().defaultBlockState());
        AlchemyArrayBlockEntity array = helper.getBlockEntity(ARRAY_POS, AlchemyArrayBlockEntity.class);
        array.inv.setStackInSlot(0, new ItemStack(NVItems.TABULA_ROBUR.get()));
        array.inv.setStackInSlot(1, new ItemStack(Items.ENDER_EYE));
        array.attemptCraft();
        if (!(array.arrayEffect instanceof AlchemyArrayEffectEnderSever)) {
            helper.fail("Tabula Robur and an Eye of Ender should make an Ender Sever Array, got " + array.arrayEffect);
            return;
        }

        Vec3 center = Vec3.atCenterOf(helper.absolutePos(ARRAY_POS));
        Vec3 near = center.add(10, 0, 0);
        Vec3 far = center.add(40, 0, 0);
        Vec3 farther = center.add(60, 0, 0);

        if (!teleportCanceled(helper, near, far)) {
            helper.fail("An enderman inside the radius should not teleport out");
            return;
        }
        if (!teleportCanceled(helper, far, near)) {
            helper.fail("An enderman outside the radius should not teleport in");
            return;
        }
        if (teleportCanceled(helper, far, farther)) {
            helper.fail("A teleport entirely outside the radius should go ahead");
            return;
        }

        helper.destroyBlock(ARRAY_POS);
        if (teleportCanceled(helper, near, far)) {
            helper.fail("Breaking the array should lift the block on teleporting");
            return;
        }
        helper.succeed();
    }

    private static boolean teleportCanceled(GameTestHelper helper, Vec3 from, Vec3 to) {
        EnderMan enderman = new EnderMan(EntityType.ENDERMAN, helper.getLevel());
        enderman.setPos(from);
        EntityTeleportEvent.EnderEntity event = new EntityTeleportEvent.EnderEntity(enderman, to.x, to.y, to.z);
        return NeoForge.EVENT_BUS.post(event).isCanceled();
    }
}
