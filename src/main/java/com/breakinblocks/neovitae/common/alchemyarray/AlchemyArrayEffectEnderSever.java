package com.breakinblocks.neovitae.common.alchemyarray;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import com.breakinblocks.neovitae.client.particle.ColoredParticleOptions;
import com.breakinblocks.neovitae.common.blockentity.AlchemyArrayBlockEntity;
import com.breakinblocks.neovitae.common.event.EnderSeverArrayHandler;
import com.breakinblocks.neovitae.common.particle.NVParticles;

public class AlchemyArrayEffectEnderSever extends AlchemyArrayEffect {

    public static final int COLOR = 0x8A2BE2;

    @Override
    public boolean update(AlchemyArrayBlockEntity tile, int ticksActive) {
        Level level = tile.getLevel();
        if (level == null || level.isClientSide()) return false;

        BlockPos pos = tile.getBlockPos();
        EnderSeverArrayHandler.register(level, pos);

        if (ticksActive % 40 == 0 && level instanceof ServerLevel serverLevel) {
            serverLevel.sendParticles(new ColoredParticleOptions(NVParticles.BLOOD_GLOW.get(), COLOR),
                    pos.getX() + 0.5, pos.getY() + 0.3, pos.getZ() + 0.5, 4, 0.3, 0.1, 0.3, 0.01);
        }
        return false;
    }

    @Override
    public void onRemoved(AlchemyArrayBlockEntity tile) {
        Level level = tile.getLevel();
        if (level != null) {
            EnderSeverArrayHandler.unregister(level, tile.getBlockPos());
        }
    }

    @Override
    public void writeToNBT(CompoundTag tag) {}

    @Override
    public void readFromNBT(CompoundTag tag) {}

    @Override
    public AlchemyArrayEffect getNewCopy() {
        return new AlchemyArrayEffectEnderSever();
    }
}
