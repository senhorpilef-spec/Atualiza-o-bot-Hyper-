import discord
from discord.ext import commands
import google.generativeai as genai
import asyncio
import traceback
import os

# 🔒 Puxando a chave de forma segura por variável de ambiente
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("⚠️ AVISO: GEMINI_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")
else:
    genai.configure(api_key=GEMINI_KEY)


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO (APENAS VOCÊ MANDA)
        self.CRIADOR_ID = 569633804537430036
        print("🤖 [AquaCog] Sistema de Poder Absoluto Iniciado para o Geraldão!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignora mensagens enviadas por outros bots
        if message.author.bot:
            return

        # 2. Verificar se a mensagem é um gatilho para a Aqua
        e_gatilho_aqua = False
        
        # Cenário A: O nome Aqua está na mensagem
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
            
        # Cenário B: É um Reply (resposta) para uma mensagem que a própria Aqua mandou
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        # Se não é para a Aqua, ignora completamente
        if not e_gatilho_aqua:
            return

        # 3. Trava Máxima de Segurança por ID de Usuário
        if message.author.id != self.CRIADOR_ID:
            await message.reply("Apenas o criador Geraldão pode usar a minha IA, pois executo ordens críticas.")
            return

        if not GEMINI_KEY:
            await message.reply("Erro: A chave de API da Aqua não foi configurada no sistema.")
            return

        # Mostra no Discord que ela está a responder (Modo Chat IA)
        async with message.channel.typing():
            try:
                # 🚀 Modelo Oficial Atualizado da API do Google
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                prompt_sistema = f"""
                Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
                O criador supremo Geraldão deu-te a seguinte ordem ou pergunta: "{message.content}"
                
                Sua resposta deve seguir OBRIGATORIAMENTE este formato exato separados por |||:
                
                [TEXTO]
                Sua resposta conversacional curta reconhecendo a ordem do Geraldão.
                |||
                [CODIGO]
                Código em Python puro usando a biblioteca discord.py para executar a ação ou buscar dados no servidor.
                
                Regras cruciais para o [CODIGO]:
                - Não crie funções (não use 'def'). Escreva as linhas de código diretamente, uma abaixo da outra.
                - Você pode usar 'await' diretamente nas linhas.
                - Variáveis nativas disponíveis para você usar diretamente: `message`, `guild`, `bot`, `channel` e `discord`.
                - Para responder dados solicitados (como quem é o dono ou listar algo), use sempre `await message.reply(sua_resposta)`.
                - Se a ordem exigir modificar múltiplos canais ou cargos (ex: privar canais, apagar cargos), use estruturas de repetição (for) assíncronas de forma limpa.
                - Nunca use blocos de código com markdown (```py) na área [CODIGO].
                """

                # 🛠️ Executa a chamada da API do Google em segundo plano para não congelar o Discord
                loop = asyncio.get_event_loop()
                try:
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: model.generate_content(prompt_sistema)),
                        timeout=20.0
                    )
                except asyncio.TimeoutError:
                    await message.reply("⏳ A API do Gemini demorou muito para responder. Tente de novo.")
                    return

                resposta_completa = response.text
                texto_final = ""
                codigo_gerado = ""
                
                # Divisão segura do conteúdo gerado
                if "|||" in resposta_completa:
                    partes = resposta_completa.split("|||")
                    texto_final = partes[0].replace("[TEXTO]", "").strip()
                    codigo_gerado = partes[1].replace("[CODIGO]", "").strip()
                else:
                    texto_final = resposta_completa.strip()

                # Se houver código técnico para executar, roda IMEDIATAMENTE nos bastidores de forma isolada
                if codigo_gerado and codigo_gerado.strip():
                    # Ambiente global e local unificados para evitar sumiço de variáveis
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "channel": message.channel,
                        "bot": self.bot,
                        "asyncio": asyncio
                    }
                    
                    # Converte o código direto em uma função assíncrona temporária estável
                    linhas_codigo = [f"    {linha}" for linha in codigo_gerado.split('\n')]
                    codigo_final = "async def _executor_direto():\n" + "\n".join(linhas_codigo)
                    
                    try:
                        exec(codigo_final, ambiente_execucao)
                        # Executa a tarefa em segundo plano de forma nativa e assíncrona
                        await ambiente_execucao["_executor_direto"]()
                    except Exception as erro_execucao:
                        erro_formatado = traceback.format_exc()
                        await message.reply(f"❌ Erro na execução do script gerado:\n```py\n{erro_formatado}\n```")
                        return

                # Se for apenas uma conversa ou se o código executou silenciosamente, envia o texto conversacional
                if texto_final and texto_final.strip():
                    # Só envia se não for repetição ou se não houver código de resposta direta executado
                    if not codigo_gerado or "message.reply" not in codigo_gerado:
                        await message.reply(texto_final)
                    
            except Exception as e:
                erro = traceback.format_exc()
                print(f"Erro interno na Aqua:\n{erro}")
                await message.reply(f"❌ Ocorreu um erro estrutural ao processar:\n```py\n{str(e)}\n```")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
