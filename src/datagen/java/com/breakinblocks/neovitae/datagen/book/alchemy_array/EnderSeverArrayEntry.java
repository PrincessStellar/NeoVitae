package com.breakinblocks.neovitae.datagen.book.alchemy_array;

import com.klikli_dev.modonomicon.api.datagen.CategoryProviderBase;
import com.klikli_dev.modonomicon.api.datagen.EntryBackground;
import com.klikli_dev.modonomicon.api.datagen.EntryProvider;
import com.klikli_dev.modonomicon.api.datagen.book.BookIconModel;
import com.klikli_dev.modonomicon.api.datagen.book.page.BookTextPageModel;
import com.klikli_dev.modonomicon.client.gui.book.theme.GuiSprite;
import com.breakinblocks.neovitae.NeoVitae;
import com.breakinblocks.neovitae.datagen.book.page.BookAlchemyArrayRecipePageModel;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Items;

public class EnderSeverArrayEntry extends EntryProvider {

    public EnderSeverArrayEntry(CategoryProviderBase parent) {
        super(parent);
    }

    @Override
    protected void generatePages() {
        this.page("intro", () -> BookTextPageModel.create()
                .withTitle(this.context().pageTitle())
                .withText(this.context().pageText()));
        this.pageTitle("Ender Sever Array");
        this.pageText("The [#](8B0000)Ender Sever Array[#]() cuts the threads an enderman pulls on when it blinks "
                + "away. While the glyph holds, no enderman can teleport out of, or into, the space within "
                + "[#](8B0000)16 blocks[#]() of it.\\n\\n"
                + "[#](8B0000)Shulkers[#]() are held just as firmly, as is any other creature that slips through "
                + "space the way endermen do.");

        this.page("usage", () -> BookTextPageModel.create()
                .withText(this.context().pageText()));
        this.pageText("Only creatures are bound. Your own [#](8B0000)Ender Pearls[#]() and "
                + "[#](8B0000)Chorus Fruit[#]() carry you as they always have.\\n\\n"
                + "The array asks nothing of your Anima once inscribed. Set one beside an enderman farm, or "
                + "wherever you would rather a struck enderman stand and fight.\\n\\n"
                + "Inscribed from a [#](8B0000)Tabula Robur[#]() and an [#](8B0000)Eye of Ender[#]() upon a "
                + "layer of Arcane Ash.");

        this.page("recipe", () -> BookAlchemyArrayRecipePageModel.create()
                .withRecipeId1(Identifier.fromNamespaceAndPath(NeoVitae.MODID, "array/ender_sever")));
    }

    @Override
    protected String entryName() {
        return "Ender Sever Array";
    }

    @Override
    protected String entryDescription() {
        return "Stops endermen and their kin from teleporting nearby.";
    }

    @Override
    protected GuiSprite entryBackground() {
        return EntryBackground.DEFAULT;
    }

    @Override
    protected BookIconModel entryIcon() {
        return BookIconModel.create(Items.ENDER_EYE);
    }

    @Override
    protected String entryId() {
        return "ender_sever_array";
    }
}
