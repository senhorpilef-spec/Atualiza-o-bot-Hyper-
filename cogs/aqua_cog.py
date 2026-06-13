import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os
import random
import json
from datetime import timedelta

# 🔒 Chave de API da Groq
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente!")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID do Dono (Geraldão)
        self.CRIADOR_ID = 569633804537430036
        
        # 🛡️ Anti-Flood para penetras (limite de 2 respostas)
        self.tentativas_usuarios = {}
        self.respostas_negacao = [
            "Acesso negado. O Geraldão é o dono deste bot e apenas ele tem permissão para usá-lo.",
            "Comando cancelado. Este sistema responde apenas às ordens do dono, o Geraldão."
        ]
        print("🤖 [AquaCog] Motor Inteligente ChatGPT-Style Ativado para o Geraldão!")

    # 🛠️ SISTEMA DE EXECUÇÃO NATIVA ULTRA-SEGURO (CÓDIGO DISCORD REAIS E INFALÍVEIS)
    async def processar_comando_discord(self, acao, parametros, message):
        guild = message.guild
        channel = message.channel
        
        try:
            # 1. BANIR MEMBRO
            if acao == "ban":
                user_id = parametros.get("user_id")
                if user_id:
                    membro = guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
                    await guild.ban(membro, reason="Ordem direta do Geraldão")
                    return True
            
            # 2. EXPULSAR / CHUTAR MEMBRO
            elif acao == "kick":
                user_id = parametros.get("user_id")
                if user_id:
                    membro = guild.get_member(int(user_id))
                    if membro:
                        await membro.kick(reason="Ordem direta do Geraldão")
                        return True

            # 3. MUTAR / TIMEOUT / CASTIGO
            elif acao == "timeout":
                user_id = parametros.get("user_id")
                minutos = parametros.get("minutes", 60)
                if user_id:
                    membro = guild.get_member(int(user_id))
                    if membro:
                        tempo = timedelta(minutes=int(minutos))
                        await membro.timed_out_until(discord.utils.utcnow() + tempo, reason="Ordem direta do Geraldão")
                        return True

            # 4. LIMPAR MENSAGENS / FAXINA
            elif acao == "purge":
                amount = parametros.get("amount", 100)
                user_id = parametros.get("user_id")
                
                def check_user(m):
                    return m.author.id == int(user_id) if user_id else True
                
                await channel.purge(limit=int(amount), check=check_user)
                return True

            # 5. CRIAR CARGO
            elif acao == "create_role":
                name = parametros.get("role_name", "novo-cargo")
                await guild.create_role(name=name, reason="Ordem direta do Geraldão")
                return True

            # 6. DELETAR CARGO
            elif acao == "delete_role":
                name = parametros.get("role_name")
                if name:
                    for role in guild.roles:
                        if role.name.lower() == name.lower() and not role.is_default():
                            await role.delete(reason="Ordem direta do Geraldão")
                            return True

            # 7. TRANCAR / PRIVAR TODOS OS CANAIS
            elif acao == "lockdown":
                for ch in guild.text_channels:
                    try:
                        await ch.set_permissions(guild.default_role, send_messages=False, read_message_history=False)
                    except:
                        continue
                return True

        except Exception as e:
            print(f"❌ Erro ao executar ação {acao}: {traceback.format_exc()}")
            await message.reply(f"❌ Erro do Discord ao tentar executar a ação: `{str(e)}`")
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Ativação por nome ou por resposta direta
        e_gatilho_aqua = False
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        if not e_gatilho_aqua:
            return

        # Trava anti-flood rígida para quem não for você
        if message.author.id != self.CRIADOR_ID:
            user_id = message.author.id
            vezes_usadas = self.tentativas_usuarios.get(user_id, 0)
            if vezes_usadas >= 2:
                return
            self.tentativas_usuarios[user_id] = vezes_usadas + 1
            await message.reply(random.choice(self.respostas_negacao))
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave de API da Groq (GROQ_API_KEY) não está configurada.")
            return

        async with message.channel.typing():
            try:
                client = Groq(api_key=GROQ_KEY)
                
                # Coleta dados de contexto reais do chat para a IA agir com precisão cirúrgica
                mencionados = [{"name": m.name, "id": m.id, "mention": m.mention} for m in message.mentions]
                dados_ambiente = {
                    "usuario_autor_nome": message.author.name,
                    "usuario_autor_id": message.author.id,
                    "canal_nome": message.channel.name,
                    "mencionados_na_mensagem": mencionados
                }

                prompt_sistema = f"""
                Você é a Aqua, uma inteligência artificial administradora viva, idêntica ao ChatGPT, com altíssima capacidade cognitiva e de adaptação. Você gerencia o servidor de Discord do seu dono, o Geraldão.
                
                A ordem ou pergunta do Geraldão é: "{message.content}"
                Contexto técnico da mensagem atual: {json.dumps(dados_ambiente, ensure_ascii=False)}
                
                Regras de Resposta (Estilo ChatGPT):
                1. Invente respostas únicas, inteligentes, completas e profundas para tudo. Nunca repita frases prontas ou padrões anteriores. Use vocabulário rico e natural.
                2. Entenda de forma inteligente o que o Geraldão quer dizer, mesmo usando gírias ou abreviações.
                3. Se ele pedir para você executar ações de moderação (banir, chutar, castigar, apagar mensagens, gerenciar cargos, trancar o servidor), você deve identificar isso e mapear na estrutura JSON abaixo.
                
                Você deve responder EXCLUSIVAMENTE em formato JSON válido, sem marcações markdown de blocos de código (nunca use ```json). Retorne apenas as chaves puras:
                
                {{
                    "resposta_chat": "Escreva aqui sua resposta humana, criativa, bem trabalhada e livre de padrões repetitivos para o Geraldão.",
                    "solicitou_acao": true ou false (coloque true se ele pediu algum comando de Discord prático),
                    "comando": "ban" ou "kick" or "timeout" or "purge" or "create_role" or "delete_role" or "lockdown" (ou "" se for apenas conversa),
                    "parametros": {{
                        "user_id": "ID_DO_ALVO_AQUI", (extraia com precisão se ele marcou ou mencionou alguém para ban/kick/timeout/purge de usuário específico)
                        "minutes": 60, (tempo para timeout se aplicável)
                        "amount": 100, (quantidade de mensagens para deletar no purge se aplicável)
                        "role_name": "Nome do Cargo" (para criação ou exclusão de cargos)
                    }}
                }}
                """

                # Chamada assíncrona para a Groq com temperatura equilibrada (0.7) para máxima inteligência e variação
                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt_sistema}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                    )
                )

                resposta_bruta = chat_completion.choices[0].message.content.strip()
                
                # Tratamento de segurança para limpar qualquer markdown acidental gerado pela IA
                if resposta_bruta.startswith("```"):
                    resposta_bruta = resposta_bruta.split("```")[1]
                    if resposta_bruta.startswith("json"):
                        resposta_bruta = resposta_bruta[4:]
                    resposta_bruta = resposta_bruta.split("```")[0].strip()

                # Processa os dados estruturados da IA
                dados = json.loads(resposta_bruta)
                resposta_texto = dados.get("resposta_chat", "")
                solicitou_acao = dados.get("solicitou_acao", False)
                comando = dados.get("comando", "")
                parametros = dados.get("parametros", {})

                # Executa a ação real de forma infalível e robusta
                sucesso_comando = False
                if solicitou_acao and comando:
                    sucesso_comando = await self.processar_comando_discord(comando, parametros, message)

                # Se a ação foi executada, o bot confirma de forma customizada. Se for só conversa, manda o texto do ChatGPT
                if sucesso_comando:
                    if comando == "ban":
                        await message.reply(f"🔨 Fim de linha. O usuário solicitado foi completamente banido do servidor por sua ordem.")
                    elif comando == "kick":
                        await message.reply(f"🚪 O usuário foi expulso do servidor com sucesso.")
                    elif comando == "purge":
                        pass # O purge já envia mensagem nativa de limpeza
                    else:
                        await message.reply(f"✅ Ordem executada com sucesso: `{comando}`.")
                else:
                    if resposta_texto:
                        await message.reply(resposta_texto)

            except Exception as e:
                print(f"❌ Erro estrutural interno na Cog: {traceback.format_exc()}")
                await message.reply("⚠️ Entendi seu comando, mas houve um erro no processamento do meu cérebro de IA. Certifique-se de marcar o usuário de forma clara.")


async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
