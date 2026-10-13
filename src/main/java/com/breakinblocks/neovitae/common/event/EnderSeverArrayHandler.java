package com.breakinblocks.neovitae.common.event;

import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityTeleportEvent;
import com.breakinblocks.neovitae.NeoVitae;
import com.breakinblocks.neovitae.client.particle.ColoredParticleOptions;
import com.breakinblocks.neovitae.common.alchemyarray.AlchemyArrayEffectEnderSever;
import com.breakinblocks.neovitae.common.blockentity.AlchemyArrayBlockEntity;
import com.breakinblocks.neovitae.common.particle.NVParticles;

import java.util.Iterator;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@EventBusSubscriber(modid = NeoVitae.MODID)
public final class EnderSeverArrayHandler {

    public static final double RADIUS = 16.0;

    private static final Set<GlobalPos> ARRAYS = ConcurrentHashMap.newKeySet();

    private EnderSeverArrayHandler() {}

    public static void register(Level level, BlockPos pos) {
        ARRAYS.add(GlobalPos.of(level.dimension(), pos.immutable()));
    }

    public static void unregister(Level level, BlockPos pos) {
        ARRAYS.remove(GlobalPos.of(level.dimension(), pos.immutable()));
    }

    public static boolean isSevered(Level level, Vec3 pos) {
        if (ARRAYS.isEmpty()) return false;
        ResourceKey<Level> dimension = level.dimension();
        Iterator<GlobalPos> it = ARRAYS.iterator();
        while (it.hasNext()) {
            GlobalPos gp = it.next();
            if (!gp.dimension().equals(dimension)) continue;

            BlockPos arrayPos = gp.pos();
            if (!level.isLoaded(arrayPos)
                    || !(level.getBlockEntity(arrayPos) instanceof AlchemyArrayBlockEntity array)
                    || !(array.arrayEffect instanceof AlchemyArrayEffectEnderSever)) {
                it.remove();
                continue;
            }

            if (Vec3.atCenterOf(arrayPos).distanceToSqr(pos) <= RADIUS * RADIUS) {
                return true;
            }
        }
        return false;
    }

    @SubscribeEvent
    public static void onEnderTeleport(EntityTeleportEvent.EnderEntity event) {
        LivingEntity entity = event.getEntityLiving();
        Level level = entity.level();
        if (level.isClientSide()) return;

        Vec3 target = new Vec3(event.getTargetX(), event.getTargetY(), event.getTargetZ());
        if (!isSevered(level, entity.position()) && !isSevered(level, target)) return;

        event.setCanceled(true);
        if (level instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(new ColoredParticleOptions(NVParticles.BLOOD_GLOW.get(), AlchemyArrayEffectEnderSever.COLOR),
                    entity.getX(), entity.getY() + entity.getBbHeight() * 0.5, entity.getZ(), 8, 0.3, 0.5, 0.3, 0.02);
        }
    }
}
